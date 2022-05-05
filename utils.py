def chunks(lst, n):
    """Yield successive n-sized chunks from lst."""
    to_return = []
    portion = len(lst) // n 
    for i in range(0, n):
        if i == (n - 1):
            last_port = lst[portion*i:]
            diff = len(last_port) - portion
            
            for j in range(diff):
                to_return[j].append(last_port[j])
                
            last_port = last_port[diff:]
            to_return.append(last_port)
            
        else:
            to_return.append(lst[portion*i: portion*(i+1)])
    return to_return