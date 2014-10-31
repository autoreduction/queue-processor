import sys

standard_vars = {
    'example integer' : 1,
    'example string' : 'Test',
    'example float' : 1.2,
}
advanced_vars = {
    'example integer list' : [1,2,3],
    'example float list' : [1.5, 2.1, 3.9],
    'example string list' : ['test1','test2'],
    'example bool' : True,
}

def extract_variables(**kwargs):
    for key in standard_vars:
        if key in kwargs:
            standard_vars[key] = parse_input_variable(standard_vars[key], kwargs[key])
    for key in advanced_vars:
        if key in kwargs:
            advanced_vars[key] = parse_input_variable(advanced_vars[key], kwargs[key])

def parse_input_variable(default, value):
    varType = type(default)
    if varType.__name__ == "str":
        return str(value)
    if varType.__name__ == "int":
        return int(value)
    if varType.__name__ == "list":
        return value.split(',')
    if varType.__name__ == "bool":
        return (value.lower() is 'true')
    if varType.__name__ == "float":
        return float(value)

def reduce():
    # Perform reduction here
    pass

def main():
    kwargs = dict(x.split('=', 1) for x in sys.argv[1:])
    extract_variables(**kwargs)
    additional_save_location = reduce()
    sys.exit(additional_save_location)

if __name__ == "__main__":
    main()