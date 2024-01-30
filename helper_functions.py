# tuple_checker.py - checks if a value exists in second pos of tuple in a list of tuples


def tuple_checker(list_of_tuples, link):
    for link_tuple in list_of_tuples:
        if link == link_tuple[1]:
            return True
    else:
        return False
