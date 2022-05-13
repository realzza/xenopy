from typing import List


def average(L, n) -> List[int]:
    """
    average the list the most possible
    """
    if (L / n) == int(L / n):
        k = int(L / n)
        ans = [k] * n
    else:
        k = int(L / n)
        a = L - k * n
        ans = [k + 1] * a + [k] * (n - a)
    return ans


def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    to_return = []
    num_list = average(len(lst), n)
    offset = 0
    for num in num_list:
        to_return.append(lst[offset : offset + num])
        offset += num
    return to_return
