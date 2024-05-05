from custom_exceptions.utils_exceptions import ClashedIdException


def gen_id(lst: list, obj_type: str) -> int:
    """Generates an ID which suits the list of given IDs to keep them increasing in order. Typically, the list is given sorted.

    Args:
        lst (list): list of IDs
        obj_type (str): the list type of IDs (file_ids, directory_ids, voice_note_ids)

    Raises:
        ClashedIdException: Incase a duplicate ID exists, Exception is raised

    Returns:
        int: the ID. If -1 is returned then file limit is reached.
    """
    if len(lst) == 0:
        return 1

    tmp_set, tmp_cache, clashed_ids = set(), [], []
    for i in lst:
        if i not in tmp_set:
            tmp_set.add(i)
            candidate = i-1
            if(candidate>0 and candidate not in tmp_set):
                tmp_cache.append(candidate)
        else:
            clashed_ids.append(i)

    if len(clashed_ids) != 0:
        raise ClashedIdException(f"{obj_type}: {str(clashed_ids)}")

    last_expected = lst[len(lst)-1]+1
    if (len(tmp_cache) != 0 and tmp_cache[0] not in tmp_set):
        return tmp_cache[0]
    elif(last_expected not in tmp_set):
        return last_expected
    else:
        ans = -1
        for i in range (last_expected+1,last_expected*65536):
            if i not in tmp_set:
                ans = i
                break
        return ans
