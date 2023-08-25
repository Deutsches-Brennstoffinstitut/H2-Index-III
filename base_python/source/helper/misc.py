def create_id(letter: str, number: int) -> str:
    import logging
    """Creates an ID consisting of 1 letter and 2 digits (3 chars in total)
    Notes:
        Single Digit Numbers are converted to a single digit number plus leading 0
    
    Warnings:
        I dont know what happens if the number is bigger than 99, added a logging warning for that
    
    Args:
        letter(str): just a letter, e.g. A, B or C
        number(int): an integer hopefully between 0 and 99
    
    Returns:
        An ID which is a string consisting of 3 Characters. 1 Letter and 2 digits.
    """
    if number > 99:
        logging.warning(f'create_id-Function got the number {number} which is greater than 99! ')
    return f'{letter}{str(number).rjust(2, str(0))}'
