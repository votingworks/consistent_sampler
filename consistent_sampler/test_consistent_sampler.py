import unittest
import random
import itertools
from consistent_sampler import sampler


def ids(n):
    id_list = [i for i in range(int(n))]
    random.shuffle(id_list)
    return id_list


class TestConsistentSampler(unittest.TestCase):
    """
    Tests based on the paper describing consistent sampling: https://arxiv.org/abs/1808.10016
    """

    def test_consistent_wrt_seed(self):
        """
        Ensure the sample results are always the same for the same seed, and
        always different for different seeds.
        """
        for n in range(1, 10):
            self.assertEqual(
                list(sampler(ids(n), 12345)),
                list(sampler(ids(n), 12345)),
            )
            self.assertNotEqual(
                list(sampler(ids(n), 12345)),
                list(sampler(ids(n), 12346)),
            )

            self.assertEqual(
                list(sampler(ids(n), 12345, take=n, with_replacement=True)),
                list(sampler(ids(n), 12345, take=n, with_replacement=True)),
            )
            self.assertNotEqual(
                list(sampler(ids(n), 12345, take=n, with_replacement=True)),
                list(sampler(ids(n), 12346, take=n, with_replacement=True)),
            )

    def test_consistent_wrt_sample_size(self):
        """
        Ensure that when drawing a small sample and a larger from the same
        list of ids, the small sample is a subset of the larger sample.

        From the paper:
            For any pool I and any seed u, we have that for any sample size s
            and s' with s' ≥ s:
                S(I, u, s) ⊆ S(I, u, s0)
            so that a larger sample is just an extension of a smaller sample.
        """
        for i in range(1, 10):
            for j in range(1, i):
                self.assertEqual(
                    list(sampler(ids(10), 12345))[:j],
                    list(sampler(ids(10), 12345))[:i][:j],
                )

        for i in range(1, 20):
            for j in range(1, i):
                self.assertEqual(
                    list(sampler(ids(10), 12345, take=j, with_replacement=True)),
                    list(sampler(ids(10), 12345, take=i, with_replacement=True))[:j],
                )

    def test_consistent_wrt_population(self):
        """
        If we draw a sample from a pool and another sample from a subset of
        that pool, the sample from the subset should equal exactly the items
        from the sample from the larger pool that are members of the subset.

        From the paper:
        For any two nonempty sets J and K with J ⊆ K, we have
            S(J , u) = S(K, u) ∩ J
        where S ∩ J denotes the subsequence of sequence S obtained by
        retaining only elements in J.
        """
        n = 10
        for i in range(1, n):
            K = random.sample(ids(n), random.randint(1, i))
            J = random.sample(K, random.randint(1, len(K)))
            self.assertEqual(
                list(sampler(J, 12345, output="id")),
                [k for k in sampler(K, 12345, output="id") if k in J],
            )
            self.assertEqual(
                list(
                    sampler(
                        J, 12345, take=len(J) * 2, with_replacement=True, output="id"
                    )
                ),
                list(
                    itertools.islice(
                        (
                            k
                            for k in sampler(
                                K, 12345, with_replacement=True, output="id"
                            )
                            if k in J
                        ),
                        len(J) * 2,
                    )
                ),
            )

    def test_take_and_drop(self):
        for n in range(1, 10):
            for d in range(1, n):
                for t in range(1, n - d):
                    self.assertEqual(
                        list(sampler(ids(n), 12345, drop=d, take=t)),
                        list(sampler(ids(n), 12345))[d : d + t],
                    )
                    self.assertEqual(
                        list(
                            sampler(
                                ids(n / 2), 12345, drop=d, take=t, with_replacement=True
                            )
                        ),
                        list(sampler(ids(n / 2), 12345, with_replacement=True, take=n))[
                            d : d + t
                        ],
                    )

    def test_ordered_by_ticket_number(self):
        for n in range(1, 10):
            sample = list(sampler(ids(n), 12345))
            self.assertEqual(sample, sorted(sample, key=lambda ticket: ticket[0]))
            sample = list(sampler(ids(n), 12345, with_replacement=True, take=n * 2))
            self.assertEqual(sample, sorted(sample, key=lambda ticket: ticket[0]))

    def test_replacement(self):
        for n in range(1, 10):
            sample = list(sampler(ids(n), 12345, with_replacement=True, take=n * 2))
            self.assertEqual(len(sample), n * 2)
            self.assertTrue(
                any(generation for (_, _, generation) in sample if generation > 1)
            )
            self.assertTrue(max(generation for (_, _, generation) in sample) <= n * 2)
            for _id, tickets in itertools.groupby(sample, key=lambda ticket: ticket[1]):
                generations = [generation for (_, _, generation) in tickets]
                self.assertEqual(generations, sorted(generations))
                self.assertEqual(generations, list(set(generations)))


if __name__ == "__main__":
    unittest.main()
