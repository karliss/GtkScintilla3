import argparse
from macpath import join
import sys
import collections
from string import Template
sys.path.append("scintilla/scripts")
import Face

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

MARSHAL_PREFIX = "gtkscintilla_marshal"

def print_evt_ctype(type):
    if type in simple_types:
        return simple_types[type]
    elif type == 'string':
        return "const char*"
    else:
        raise Exception("Unrecognised type: " + type)

def split_name(name):
    result = ""
    for c in name:
        if c.isupper():
            result += "_"
        result += c.lower()
    return result.lstrip("_")

def fix_name(name, long_name=False):
    patterns = long_names if long_name else short_names
    for pattern in patterns:
        name = name.replace(pattern, patterns[pattern])
    return "_" + split_name(name)

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

def print_event_class_decls(events):
    result = ""
    for name, event in events:
        result += "void (*" + split_name(name) + ")("
        result += ", ".join([print_evt_ctype(i[0]) + " "+  i[1] for i in event["Param"]])
        result += ");\n"
    return result

def print_evt_enum(events):
    result = ""
    for name, obj in events:
        result += "    " + split_name(name).upper() + ",\n"
    return result

def print_evt_gtype(name, param):
    #TODO: MacroRecord types could pointers
    return param[0].upper()

def print_marshal(name, param):
    result = ""
    if len(param) <= 1:
        result = "g_cclosure_marshal_VOID_"
    else:
        result = MARSHAL_PREFIX + "_VOID_"
    if len(param) == 0:
        result += "_VOID"
    for p in param:
        result += "_" + print_evt_gtype(name, p)
    return result


def print_evt_signal_array(events):
    result = ''
    for name, event in events:
        underscore_name = split_name(name).lower()
        result += '    signals[' + underscore_name.upper() + '] =\n' \
                  '        g_signal_new("' + underscore_name + '",\n' \
                  '                     G_OBJECT_CLASS_TYPE (class),\n' \
                  '                     G_SIGNAL_RUN_FIRST,\n' \
                  '                     G_STRUCT_OFFSET (GtkScintillaClass, ' + underscore_name + '),\n' \
                  '                     NULL, NULL,\n' \
                  '                     ' + print_marshal(name, event['Param']) + ',\n' \
                  '                     G_TYPE_NONE, ' + str(len(event['Param']))

        for param in event['Param']:
            result += ',\n'
            result += '                     G_TYPE_' + print_evt_gtype(name, param)
        result += ');\n'
    return result

def print_evt_forward(events):
    result = ""
    for name, event in events:
        result += '    case SCN_' + name.upper() + ':\n' \
                  '    {\n' \
                  '        g_signal_emit(self,\n' \
                  '                      signals[' + split_name(name).upper() + '], 0'
        for type, pname in event['Param']:
            result += ',\n                      (' + print_evt_ctype(type) + ') notification->' + pname
        result += ');\n' \
                  '        break;\n' \
                  '    }\n'
    return result

def get_events(features):
    result = []
    for name, obj in features.items():
        if obj["FeatureType"] != "evt":
            continue
        result.append( (name, obj) )
    return result;

def process_template(template, output_name, values):
    input = open(template)
    output = open(output_name,'w')
    src = Template(input.read())
    output.write(src.substitute(values))
    output.close()
    input.close()

def generate_c_files(opts, face):
    processed = set([])

    features = face.features

    events = get_events(features)

    process_template("src/gtkscintilla.h.template", "src/gtkscintilla.h",
        {
            "event_decl" : print_event_class_decls(events),
            "function_decl" : print_functions(opts, features, processed, False),
        })

    process_template("src/gtkscintilla.c.template", "src/gtkscintilla.c",
        {
            'function_def' : print_functions(opts, features, processed, True),
            'evt_enum' : print_evt_enum(events),
            'evt_signals_array' : print_evt_signal_array(events),
            'evt_forward' : print_evt_forward(events),
        })
   #              "/* ", True, [print_event_class_decls(events)], [print_functions(opts, features, processed, False)])
    #GenerateFile(
    #             "/* ", True, [print_functions(opts, features, processed, True)])

    unprocessed = len(features) - len(processed)
    if unprocessed > 0:
        print(unprocessed, "symbols were unprocessed")

    if (opts.verbose):
        for name, obj in features.items():
            if name not in processed:
                print(obj["FeatureType"], name)

def generate_marshal(opts, face):
    events = get_events(face.features)
    out = open("marshal.list", "w")
    for name, event in events:
        if len(event["Param"]) <= 1:
            #use builtin marshaller
            continue
        out.write("VOID:")
        out.write(",".join([print_evt_gtype(name, i) for i in event["Param"]]))
        out.write("\n")
    out.close()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--iface", default="./scintilla/include/Scintilla.iface", help="Scintilla.iface file")
    parser.add_argument("--mode", "-m", default="c", choices=["c", "marshal"])
    parser.add_argument("--long_names", action="store_true", default=False, help="use long name, e.g. auto_correct instead of autoc")
    parser.add_argument("--verbose", "-v", action="store_true", default=False, help="Verbose mode")

    opts = parser.parse_args()

    print(opts.iface)
    print(opts.mode)

    face = read_face(opts.iface)

    if opts.mode == "c":
        generate_c_files(opts, face)
    elif opts.mode == "marshal":
        generate_marshal(opts, face)
    else:
        raise Exception("Unexpected mode: " + opts.mode)


if __name__ == "__main__":
    main()
