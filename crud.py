# -*- coding: utf-8 -*-
import sys
import os
import base

from ptsd import ast
from ptsd.loader import Loader, Parser
from Cheetah.Template import Template
from os import path

if len(sys.argv) != 3:
	print "usage: \n\tpython crud.py thrift_file_path output_folder_path"
	sys.exit()

thrift_file = sys.argv[1]
out_path = sys.argv[2]
filename = ".".join(path.basename(thrift_file).split(".")[:-1])

if not out_path.endswith(path.sep):
    out_path = out_path + path.sep

outDir = out_path.split(path.sep)[-2]

def updateController(out_path):
    subdirs = [o for o in os.listdir(out_path) if os.path.isdir(os.path.join(out_path, o))]
    content = "package controller\n\nimport (\n"
    for x in subdirs:
        l = "\t_ \"controller/{0}\"\n".format(x)
        content = content + l

    content = content + ")\n"
    f = open(out_path + "gen_init.go", "w")
    f.write(content)
    f.close()

def getControlDir(urlBase):
    outdir = out_path + urlBase.split(path.sep)[-2] + path.sep
    if not os.path.exists(outdir):
        os.makedirs(outdir)
    return outdir

def fieldElem(field, key):
    for att in field.annotations:
        if att.name.value.lower() == key:
            return att.value.value
    return ""

def fieldElems(field, key):
    key = key.lower()
    ret = []
    for att in field.annotations:
        if att.name.value.lower() == key:
            ret.append(att.value.value)
    return ret

def transform_module(module):
    for obj in module.structs:
        urlBase = ""
        obj.imports = set()
        idField = obj.fields[0]
        urlBase = fieldElem(idField, "baseurl")
        tplPackage = fieldElem(idField, "tplpackage")

        if tplPackage == "":
            tplPackage = "tpl/auto"

        if urlBase == "":
            continue

        if obj.label != obj.name.value:
            obj.imports.add("admin/permission")
            obj.hasUser = len([i for i in obj.fields if str(i.name) == "UsersID"]) > 0

            if len(obj.relateObj) > 0:
                obj.imports.add("encoding/json")

            outDir = urlBase.split(path.sep)[-2]
            crud = open('tmpl/crud.tmpl', 'r').read().decode("utf8")
            res = Template(crud, searchList=[{"namespace": outDir,
                                            "className": obj.name.value,
                                            "urlBase": urlBase,
                                            "tplPackage": tplPackage,
                                            "obj": obj,
                                            }])
            writeDir = getControlDir(urlBase)
            outfile = writeDir + "gen_" + obj.name.value.lower() + ".go"
            with open(outfile, "w") as fp:
                fp.write(str(res))
        else:
            for field in obj.fields:
                if field.widget_type in ("relateSelect", "relateAjaxSelect"):
                    outDir = urlBase.split(path.sep)[-2]
                    tmpl = file("tmpl/relateOnly.tmpl").read().decode("u8")
                    ret = Template(tmpl, searchList=[{"namespace": outDir,
                                            "className": obj.label,
                                            "urlBase": urlBase,
                                            "tplPackage": tplPackage,
                                            "obj": obj,
                                            }])
                    writeDir = getControlDir(urlBase)
                    outfile = writeDir + "gen_relate_" + obj.name.value.lower() + ".go"
                    with open(outfile, "w") as fp:
                        fp.write(str(ret).strip())
                    break


def main(thrift_idl):
    loader = base.load_thrift(thrift_idl)
    global namespace
    namespace = loader.namespace
    for obj in loader.modules.values():
        transform_module(obj)
    updateController(out_path)

main(thrift_file)
