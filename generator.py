import argparse
import sys
import collections

sys.path.append("scintilla/scripts")
import Face
from FileGenerator import GenerateFile


def read_face(file_name):
    face = Face.Face()
    face.ReadFromFile(file_name)
    return face


simple_types = {
    "void": "void",
    "int": "gint",
    "bool": "gboolean",
    "position" : "gint", #TODO: changeable position type
    "colour" : "gint", #TODO: better color handling
}

# For comaptibility with other gtk scintila libraries
short_names = {
    'WS' : 'Ws',
    'EOL' : 'Eol',
    'AutoC' : 'Autoc',
    'KeyWords' : 'Keywords',
    'BackSpace' : 'Backspace',
    'UnIndents' : 'Unindents',
    'TargetRE' : 'TargetRe',
    'RGBA' : 'Rgba',
}

long_names = {
    'WS' : 'WhiteSpace',
    'EOL' : 'Eol',
    'AutoC' : 'AutoCompletion',
    'KeyWords' : 'Keywords',
    'BackSpace' : 'Backspace',
    'UnIndents' : 'Unindents',
    'TargetRE' : 'TargetRe',
    'RGBA' : 'Rgba',
    'VScrollBar': 'Vscrollbar',
    'VC' : 'VisibleChar',
}

def fix_name(name, long_name=False):
    #TODO: capitalBlocks
    patterns = long_names if long_name else short_names
    for pattern in patterns:
        name = name.replace(pattern, patterns[pattern])
    result = ""
    for c in name:
        if c.isupper():
            result += "_"
        result += c.lower()
    print (result)
    return result


def convert_type(type):
    if not type:
        return ""

    if type in simple_types:
        return simple_types[type]
    return None


def known_type(type):
    return type != None


Arg = collections.namedtuple("Arg", ["name", "type", "value"])


def print_simple_arg(arg):
    if arg.type:
       return ", " + arg.type + " " + arg.name
    return ""

def use_simple_arg(arg, pos):
    if arg.type:
        return ", " + arg.name
    else:
        return ", 0"

def print_function(opts, name, function, body):
    ret_type = convert_type(function["ReturnType"])
    type1 = convert_type(function["Param1Type"])
    type2 = convert_type(function["Param2Type"])

    arg = [
        Arg(function["Param1Name"], type1, function["Param1Value"]),
        Arg(function["Param2Name"], type2, function["Param2Value"]),
    ]

    if not (known_type(ret_type) and known_type(type1) and known_type(type2)):
        return None

    result = ""

    result += ret_type + " gtk_scintilla" + fix_name(name, opts.long_names) + "(GtkScintilla *sci"
    result += print_simple_arg(arg[0]) + print_simple_arg(arg[1])
    result += ")";

    if not body:
        result += ";\n"
    else:
        result += "\n{\n"
        result += "    "
        if ret_type != "void":
            result += "return "
        result += "scintilla_send_message(SCINTILLA(sci), " + function["Value"]
        result += use_simple_arg(arg[0], 0) + use_simple_arg(arg[1], 1)
        result += ");\n"
        result += "}\n"

    return result


def print_functions(opts, features, processed, body=False):
    result = ""
    for name, obj in features.items():
        type = obj["FeatureType"]
        if type != "fun" and type != "get" and type != "set":
            continue

        func = print_function(opts, name, obj, body)
        if func:
            processed.add(name)
            result += func

    #print(result)
    return result



def generate_c_files(opts, face):
    processed = set([])

    features = face.features

    GenerateFile("src/gtkscintilla.h.template", "src/gtkscintilla.h",
			     "/* ", True, [print_functions(opts, features, processed, False)])
    GenerateFile("src/gtkscintilla.c.template", "src/gtkscintilla.c",
			     "/* ", True, [print_functions(opts, features, processed, True)])

    unprocessed = len(features) - len(processed)
    if unprocessed > 0:
        print(unprocessed, "symbols were unprocessed")

    if (opts.verbose):
        for name, obj in features.items():
            if name not in processed:
                print(obj["FeatureType"], name)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iface", default="./scintilla/include/Scintilla.iface", help="Scintilla.iface file")
    parser.add_argument("--mode", "-m", default="c", choices=["c"])
    parser.add_argument("--long_names", action="store_true", default=False, help="use long name, e.g. auto_correct instead of autoc")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Verbose mode")

    opts = parser.parse_args()

    print(opts.iface)
    print(opts.mode)

    face = read_face(opts.iface)

    if opts.mode == "c":
        generate_c_files(opts, face)
    else:
        raise Exception("Unexpected mode: " + opts.mode)


if __name__ == "__main__":
    main()
