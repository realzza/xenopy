def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    portion = len(lst) // n 
    for i in range(0, n):
        if i == (n - 1):
            yield lst[portion*i:]
        else:
            yield lst[portion*i: portion*(i+1)]