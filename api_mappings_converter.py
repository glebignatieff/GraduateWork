import os
import sqlite3


axplorer = 'mappings/axplorer/permissions/'
pscout = 'mappings/PScout/permissions/'


# Permissions
normal_perms = 'data/permissions/normal.txt'
signature_perms = 'data/permissions/signature.txt'
dangerous_perms = 'data/permissions/dangerous.txt'


PRIMITIVE_TYPES = {
    'void':     'V',
    'boolean':  'Z',
    'byte':     'B',
    'short':    'S',
    'char':     'C',
    'int':      'I',
    'long':     'J',
    'float':    'F',
    'double':   'D'
}


# Converts Java types to Smali
def to_smali_type(java_type):
    ret = None
    narrays = 0

    # check if it's an array
    if java_type.endswith('[]'):
        narrays = java_type.count('[]')
        java_type = java_type.rstrip('[]')

    # if it's a class
    if '.' in java_type:
        smali_type = 'L' + java_type.replace('.', '/') + ';'
    # if it's a simple type
    elif java_type in PRIMITIVE_TYPES:
        smali_type = PRIMITIVE_TYPES[java_type]

    # if it's an array - add [ before type
    ret = ('[' * narrays) + smali_type

    return ret


# def get_permissions():
#     ret = {}

#     with open(normal_perms) as f:
#         ret['normal'] = f.read().split('\n')
#     with open(dangerous_perms) as f:
#         ret['dangerous'] = f.read().split('\n')
#     with open(signature_perms) as f:
#         ret['signature'] = f.read().split('\n')

#     return ret


def parse_pscout_line(line):
    ret = {}

    if line.startswith('Permission'):
        ret['permission'] = line.strip().split(':')[-1]
    elif line.startswith('<'):
        strs = line.split(' ')

        # class name
        class_name = to_smali_type(strs[0].strip('<:'))
        if not class_name.startswith('Landroid'):
            return ret

        # return type
        ret_type = to_smali_type(strs[1])

        # method := name + args
        method = strs[2].rstrip('>')
        method_name, args = method.rstrip(')').split('(')
        arg_list = []
        if len(args) != 0:
            for arg in args.split(','):
                smali_arg = to_smali_type(arg)
                arg_list.append(smali_arg)

        smali_api = class_name + '->' + method_name +\
            '(' + ' '.join(arg_list) + ')' + ret_type

        ret['api'] = smali_api

    return ret


def parse_axplorer_line(line):
    api, permissions = map(str.strip, line.split('::'))
    strs = api.split('(')
    args, ret_type = strs[1].split(')')

    # return type + axplorer bug fix
    if ret_type.endswith('[]'):
        ret_type = '[' * ret_type.count('[]') + ret_type.rstrip('[]')
    else:
        ret_type = to_smali_type(ret_type)

    # arguments
    arg_list = []
    if len(args) != 0:
        for arg in args.split(','):
            # argument type conversion + axplorer bug fix
            if arg.startswith('['):
                smali_arg = '[' * arg.count('[') + to_smali_type(arg.lstrip('['))
            else:
                smali_arg = to_smali_type(arg)
            arg_list.append(smali_arg)

    # class and method name
    strs = strs[0].split('.')
    method_name = strs[-1]
    class_name = to_smali_type('.'.join(strs[:-1]))

    smali_api = class_name + '->' + method_name +\
        '(' + ' '.join(arg_list) + ')' + ret_type

    ret = {'permissions': permissions.split(', '), 'api': smali_api}
    return ret


def create_table_with_pk(cursor, table_name, header, pk):
    query = 'CREATE TABLE IF NOT EXISTS {} ({}, PRIMARY KEY({}))'.format(
        table_name, ','.join(header), ','.join(pk))
    cursor.execute(query)


def insert_row(cursor, table_name, values):
    query = 'INSERT INTO {} VALUES ({})'.format(table_name, ','.join(values))
    cursor.execute(query)


def pscout_to_sqlite(sqlite3_cursor):
    for pscout_api in os.listdir(pscout):
        pscout_mappings = os.path.join(pscout, pscout_api, 'allmappings')
        table_name = '_'.join(['PSCOUT', pscout_api])
        create_table_with_pk(sqlite3_cursor, table_name, ['api', 'permission'], ['api', 'permission'])
        with open(pscout_mappings) as f:
            current_perm = None
            for line in f:
                ret = parse_pscout_line(line)
                if 'permission' in ret:
                    current_perm = ret['permission']
                elif 'api' in ret:
                    api = ret['api']
                    insert_row(sqlite3_cursor, table_name, ['\'' + api + '\'', '\'' + current_perm + '\''])
        print('PScout: %s is done' % pscout_api)


def axplorer_to_sqlite(sqlite3_cursor):
    for axplorer_api in os.listdir(axplorer):
        axplorer_mappings = os.path.join(axplorer, axplorer_api,
                                         'sdk-map-' + axplorer_api.split('_')[-1] + '.txt')
        table_name = '_'.join(['AXPLORER', axplorer_api])
        create_table_with_pk(sqlite3_cursor, table_name, ['api', 'permission'], ['api', 'permission'])
        with open(axplorer_mappings) as f:
            for line in f:
                ret = parse_axplorer_line(line)
                for perm in ret['permissions']:
                    insert_row(sqlite3_cursor, table_name, ['\'' + ret['api'] + '\'', '\'' + perm + '\''])
        print('axplorer: %s is done' % axplorer_api)


if __name__ == '__main__':
    with sqlite3.connect('mapping.db') as conn:
        cursor = conn.cursor()

        # PScout
        pscout_to_sqlite(cursor)
        conn.commit()

        # axplorer
        axplorer_to_sqlite(cursor)
        conn.commit()
