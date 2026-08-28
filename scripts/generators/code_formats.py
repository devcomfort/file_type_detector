"""Code format generators."""

from .base import BaseGenerator
from . import register


@register
class CodeFormatGenerator(BaseGenerator):
    """Generates minimal valid source code files."""

    @property
    def extensions(self) -> list[str]:
        return [
            "py",
            "pyi",
            "js",
            "mjs",
            "cjs",
            "ts",
            "mts",
            "cts",
            "tsx",
            "mtsx",
            "ctsx",
            "jsx",
            "mjsx",
            "cjsx",
            "java",
            "kt",
            "kts",
            "scala",
            "rb",
            "php",
            "sh",
            "lua",
            "swift",
            "go",
            "rs",
            "c",
            "cc",
            "cxx",
            "cpp",
            "c++",
            "cppm",
            "ixx",
            "h",
            "hh",
            "hpp",
            "hxx",
            "h++",
            "cs",
            "csx",
            "m",
            "mm",
            "f90",
            "f95",
            "f03",
            "v",
            "verilog",
            "vlg",
            "vh",
            "vhd",
            "sql",
            "pl",
            "pro",
            "p",
            "pas",
            "pp",
            "jl",
            "R",
            "dart",
            "ex",
            "exs",
            "erl",
            "hrl",
            "hs",
            "lhs",
            "ml",
            "mli",
            "lisp",
            "lsp",
            "l",
            "cl",
            "scm",
            "ss",
            "coffee",
            "sol",
            "yar",
            "yara",
            "hcl",
            "proto",
            "textproto",
            "textpb",
            "pbtxt",
            "cmake",
            "gradle",
            "groovy",
            "bzl",
            "gemspec",
            "au3",
            "awk",
            "hbs",
            "handlebars",
            "jinja",
            "jinja2",
            "j2",
            "scss",
            "odin",
            "gleam",
            "ipynb",
            "tcl",
            "m4",
            "bf",
            "b",
            "smali",
            "abnf",
            "aidl",
            "gpx",
            "xsd",
            "htm",
            "xhtml",
            "xht",
            "tsv",
            "jsonld",
            "yml",
            "s",
            "S",
            "asm",
            "cob",
            "cpy",
            "cbl",
            "CBL",
            "COB",
            "CPY",
            "F90",
            "P",
            "a68",
            "html",
            "css",
            "json",
            "jsonl",
            "svg",
            "yaml",
            "toml",
            "ini",
            "dockerfile",
            "makefile",
            "bat",
            "ps1",
            "vbs",
            "ksh",
            "ahk",
            "erb",
            "vue",
            "clj",
            "litcoffee",
            "elm",
            "nix",
            "tf",
            "vim",
            "aff",
            "zig",
            "csproj",
            "vcxproj",
            "hta",
            "jnlp",
            "twig",
            "vba",
            "mht",
            "raku",
            "raku6",
            "p6",
            "pl6",
            "pm6",
            "cabal",
            "dhall",
            "purs",
            "agda",
            "idr",
            "lean",
            "roc",
            "mojo",
            "carbon",
            "move",
            "cairo",
            "wgsl",
            "glsl",
            "hlsl",
            "metal",
            "spv",
            "mlir",
            "firrtl",
            "chisel",
            "bluespec",
            "vb",
            "vbe",
            "asp",
            "aspx",
            "matlab",
            "cljr",
            "cljs",
            "r",
            "rust",
            "po",
            "pot",
            "csv",
            "xml",
        ]

    @property
    def sources(self) -> dict[str, str]:
        base = {
            ext: "synthetic:Minimal valid source code"
            for ext in [
                "py",
                "pyi",
                "js",
                "mjs",
                "cjs",
                "ts",
                "mts",
                "cts",
                "tsx",
                "mtsx",
                "ctsx",
                "jsx",
                "mjsx",
                "cjsx",
                "java",
                "kt",
                "kts",
                "scala",
                "rb",
                "php",
                "sh",
                "lua",
                "swift",
                "go",
                "rs",
                "c",
                "cc",
                "cxx",
                "cpp",
                "c++",
                "cppm",
                "ixx",
                "h",
                "hh",
                "hpp",
                "hxx",
                "h++",
                "cs",
                "csx",
                "m",
                "mm",
                "f90",
                "f95",
                "f03",
                "v",
                "verilog",
                "vlg",
                "vh",
                "vhd",
                "sql",
                "pl",
                "pro",
                "p",
                "pas",
                "pp",
                "jl",
                "R",
                "dart",
                "ex",
                "exs",
                "erl",
                "hrl",
                "hs",
                "lhs",
                "ml",
                "mli",
                "lisp",
                "lsp",
                "l",
                "cl",
                "scm",
                "ss",
                "coffee",
                "sol",
                "yar",
                "yara",
                "hcl",
                "proto",
                "textproto",
                "textpb",
                "pbtxt",
                "cmake",
                "gradle",
                "groovy",
                "bzl",
                "gemspec",
                "au3",
                "awk",
                "hbs",
                "handlebars",
                "jinja",
                "jinja2",
                "j2",
                "scss",
                "odin",
                "gleam",
                "ipynb",
                "tcl",
                "m4",
                "bf",
                "b",
                "smali",
                "abnf",
                "aidl",
                "gpx",
                "xsd",
                "htm",
                "xhtml",
                "xht",
                "tsv",
                "jsonld",
                "yml",
                "s",
                "S",
                "asm",
                "cob",
                "cpy",
                "cbl",
                "CBL",
                "COB",
                "CPY",
                "F90",
                "P",
                "a68",
            ]
        }
        base.update(
            {
                "html": "synthetic:HTML5 document",
                "css": "synthetic:CSS stylesheet",
                "json": "synthetic:JSON data",
                "jsonl": "synthetic:JSON Lines",
                "svg": "synthetic:SVG image",
                "yaml": "synthetic:YAML config",
                "toml": "synthetic:TOML config",
                "ini": "synthetic:INI config",
                "dockerfile": "synthetic:Dockerfile",
                "makefile": "synthetic:Makefile",
                "bat": "synthetic:Windows batch",
                "ps1": "synthetic:PowerShell",
                "ahk": "synthetic:AutoHotkey",
                "vbs": "synthetic:VBScript",
                "ksh": "synthetic:Korn shell",
                "erb": "synthetic:ERB template",
                "vue": "synthetic:Vue SFC",
                "clj": "synthetic:Clojure",
                "litcoffee": "synthetic:Literate CoffeeScript",
                "elm": "synthetic:Elm",
                "nix": "synthetic:Nix",
                "tf": "synthetic:Terraform HCL",
                "vim": "synthetic:Vim script",
                "aff": "synthetic:Hunspell affix",
                "zig": "synthetic:Zig",
                "csproj": "synthetic:C# project XML",
                "vcxproj": "synthetic:C++ project XML",
                "hta": "synthetic:HTML Application",
                "jnlp": "synthetic:Java Web Start XML",
                "twig": "synthetic:Twig template",
                "vba": "synthetic:VBA",
                "mht": "synthetic:MHTML",
                "raku": "synthetic:Raku",
                "raku6": "synthetic:Raku",
                "p6": "synthetic:Raku",
                "pl6": "synthetic:Raku",
                "pm6": "synthetic:Raku",
                "cabal": "synthetic:Cabal",
                "dhall": "synthetic:Dhall",
                "purs": "synthetic:PureScript",
                "agda": "synthetic:Agda",
                "idr": "synthetic:Idris",
                "lean": "synthetic:Lean",
                "roc": "synthetic:Roc",
                "mojo": "synthetic:Mojo",
                "carbon": "synthetic:Carbon",
                "move": "synthetic:Move",
                "cairo": "synthetic:Cairo",
                "wgsl": "synthetic:WGSL",
                "glsl": "synthetic:GLSL",
                "hlsl": "synthetic:HLSL",
                "metal": "synthetic:Metal",
                "spv": "synthetic:SPIR-V",
                "mlir": "synthetic:MLIR",
                "firrtl": "synthetic:FIRRTL",
                "chisel": "synthetic:Chisel",
                "bluespec": "synthetic:Bluespec",
                "vb": "synthetic:Minimal valid Visual Basic source code",
                "vbe": "synthetic:Minimal valid encrypted VBScript",
                "asp": "synthetic:Minimal valid ASP source",
                "aspx": "synthetic:Minimal valid ASP.NET source",
                "matlab": "synthetic:Minimal valid MATLAB source",
                "cljr": "synthetic:Minimal valid ClojureScript (CLJR) source",
                "cljs": "synthetic:Minimal valid ClojureScript source",
                "r": "synthetic:Minimal valid R source (lowercase extension)",
                "rust": "synthetic:Minimal valid Rust source",
                "po": "synthetic:Minimal valid gettext PO translation",
                "pot": "synthetic:Minimal valid gettext PO template",
                "csv": "synthetic:Minimal valid CSV data",
                "xml": "synthetic:Minimal valid XML document",
            }
        )
        return base

    @property
    def category(self) -> str:
        return "code"

    def generate(self, ext: str) -> bytes:
        generators = {
            "py": self._py,
            "pyi": self._pyi,
            "js": self._js,
            "mjs": self._js,
            "cjs": self._js,
            "ts": self._ts,
            "mts": self._ts,
            "cts": self._ts,
            "tsx": self._tsx,
            "mtsx": self._tsx,
            "ctsx": self._tsx,
            "jsx": self._jsx,
            "mjsx": self._jsx,
            "cjsx": self._jsx,
            "java": self._java,
            "kt": self._kt,
            "kts": self._kt,
            "scala": self._scala,
            "rb": self._rb,
            "php": self._php,
            "sh": self._sh,
            "lua": self._lua,
            "swift": self._swift,
            "go": self._go,
            "rs": self._rs,
            "c": self._c,
            "cc": self._cpp,
            "cxx": self._cpp,
            "cpp": self._cpp,
            "c++": self._cpp,
            "cppm": self._cpp,
            "ixx": self._cpp,
            "h": self._h,
            "hh": self._hpp,
            "hpp": self._hpp,
            "hxx": self._hpp,
            "h++": self._hpp,
            "cs": self._cs,
            "csx": self._cs,
            "m": self._objc,
            "mm": self._objc,
            "f90": self._fortran,
            "f95": self._fortran,
            "f03": self._fortran,
            "v": self._verilog,
            "verilog": self._verilog,
            "vlg": self._verilog,
            "vh": self._verilog,
            "vhd": self._vhdl,
            "sql": self._sql,
            "pl": self._perl,
            "pro": self._prolog,
            "p": self._prolog,
            "pas": self._pascal,
            "pp": self._pascal,
            "jl": self._julia,
            "R": self._r,
            "dart": self._dart,
            "ex": self._elixir,
            "exs": self._elixir,
            "erl": self._erlang,
            "hrl": self._erlang_hrl,
            "hs": self._haskell,
            "lhs": self._haskell_lhs,
            "ml": self._ocaml,
            "mli": self._ocaml_mli,
            "lisp": self._lisp,
            "lsp": self._lisp,
            "l": self._lisp,
            "cl": self._lisp,
            "scm": self._scheme,
            "ss": self._scheme,
            "coffee": self._coffee,
            "sol": self._solidity,
            "yar": self._yara,
            "yara": self._yara,
            "hcl": self._hcl,
            "proto": self._proto,
            "textproto": self._textproto,
            "textpb": self._textproto,
            "pbtxt": self._textproto,
            "cmake": self._cmake,
            "gradle": self._gradle,
            "groovy": self._groovy,
            "bzl": self._bzl,
            "gemspec": self._gemspec,
            "au3": self._autoit,
            "awk": self._awk,
            "hbs": self._handlebars,
            "handlebars": self._handlebars,
            "jinja": self._jinja,
            "jinja2": self._jinja,
            "j2": self._jinja,
            "scss": self._scss,
            "odin": self._odin,
            "gleam": self._gleam,
            "ipynb": self._ipynb,
            "tcl": self._tcl,
            "m4": self._m4,
            "bf": self._brainfuck,
            "b": self._brainfuck,
            "smali": self._smali,
            "abnf": self._abnf,
            "aidl": self._aidl,
            "gpx": self._gpx,
            "xsd": self._xsd,
            "htm": self._html,
            "xhtml": self._html,
            "xht": self._html,
            "tsv": self._tsv,
            "jsonld": self._jsonld,
            "yml": self._yaml,
            "s": self._asm,
            "S": self._asm,
            "asm": self._asm,
            "cob": self._cobol,
            "cpy": self._cobol,
            "cbl": self._cobol,
            "html": self._html,
            "css": self._css,
            "json": self._json,
            "jsonl": self._jsonl,
            "svg": self._svg,
            "yaml": self._yaml,
            "toml": self._toml,
            "ini": self._ini,
            "dockerfile": self._dockerfile,
            "makefile": self._makefile,
            "bat": self._bat,
            "ps1": self._ps1,
            "vbs": self._vbs,
            "ksh": self._ksh,
            "ahk": self._ahk,
            "erb": self._erb,
            "vue": self._vue,
            "clj": self._clj,
            "litcoffee": self._litcoffee,
            "elm": self._elm,
            "nix": self._nix,
            "tf": self._tf,
            "vim": self._vim,
            "aff": self._aff,
            "zig": self._zig,
            "csproj": self._csproj,
            "vcxproj": self._vcxproj,
            "hta": self._hta,
            "jnlp": self._jnlp,
            "twig": self._twig,
            "vba": self._vba,
            "mht": self._mht,
            "raku": self._raku,
            "raku6": self._raku,
            "p6": self._raku,
            "pl6": self._raku,
            "pm6": self._raku,
            "cabal": self._cabal,
            "dhall": self._dhall,
            "purs": self._purs,
            "agda": self._agda,
            "idr": self._idr,
            "lean": self._lean,
            "roc": self._roc,
            "mojo": self._mojo,
            "carbon": self._carbon,
            "move": self._move,
            "cairo": self._cairo,
            "wgsl": self._wgsl,
            "glsl": self._glsl,
            "hlsl": self._hlsl,
            "metal": self._metal,
            "spv": self._spv,
            "mlir": self._mlir,
            "firrtl": self._firrtl,
            "chisel": self._chisel,
            "bluespec": self._bluespec,
            "vb": self._vb,
            "vbe": self._vbe,
            "asp": self._asp,
            "aspx": self._aspx,
            "matlab": self._matlab,
            "cljr": self._cljr,
            "cljs": self._cljs,
            "CBL": self._cobol_upper,
            "COB": self._cobol_upper,
            "CPY": self._cobol_copy_upper,
            "F90": self._fortran,
            "P": self._prolog_upper,
            "a68": self._algol68,
            "r": self._r_lower,
            "rust": self._rs,
            "po": self._po,
            "pot": self._pot,
            "csv": self._csv,
            "xml": self._xml,
        }
        return generators[ext]().encode("utf-8")

    def _py(self) -> str:
        return '#!/usr/bin/env python3\n"""Sample."""\n\ndef main():\n    print("Hello")\n\nif __name__ == "__main__":\n    main()\n'

    def _pyi(self) -> str:
        return "def greet(name: str) -> str: ...\n"

    def _js(self) -> str:
        return '"use strict";\n\nfunction main() {\n    console.log("Hello");\n}\n\nmain();\n'

    def _ts(self) -> str:
        return "// Sample TypeScript file\ninterface Greeting {\n    name: string;\n    age: number;\n}\n\nfunction greet({ name, age }: Greeting): string {\n    return `Hello, ${name}! You are ${age} years old.`;\n}\n\nconst user: Greeting = { name: 'World', age: 25 };\nconsole.log(greet(user));\n"

    def _tsx(self) -> str:
        return 'import React from "react";\n\ninterface Props {\n    message: string;\n}\n\nexport const App: React.FC<Props> = ({ message }) => {\n    return <h1>{message}</h1>;\n};\n'

    def _jsx(self) -> str:
        return 'import React from "react";\n\nexport const App = ({ message }) => {\n    return <h1>{message}</h1>;\n};\n\nexport default App;\n'

    def _java(self) -> str:
        return 'public class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello");\n    }\n}\n'

    def _kt(self) -> str:
        return 'data class Greeting(val name: String, val age: Int)\n\nfun greet(g: Greeting): String {\n    return "Hello, ${g.name}! You are ${g.age} years old."\n}\n\nfun main() {\n    val g = Greeting("World", 25)\n    println(greet(g))\n}\n'

    def _scala(self) -> str:
        return 'case class Greeting(name: String, age: Int)\n\nobject Main {\n  def greet(g: Greeting): String =\n    s"Hello, ${g.name}! You are ${g.age} years old."\n\n  @main def main(): Unit =\n    val g = Greeting("World", 25)\n    println(greet(g))\n}\n'

    def _rb(self) -> str:
        return '# Sample Ruby file\nclass Greeting\n  attr_reader :name, :age\n\n  def initialize(name, age)\n    @name = name\n    @age = age\n  end\n\n  def message\n    "Hello, #{@name}! You are #{@age} years old."\n  end\nend\n\ng = Greeting.new("World", 25)\nputs g.message\n'

    def _php(self) -> str:
        return '<?php\necho "Hello\\n";\n?>\n'

    def _sh(self) -> str:
        return '#!/bin/bash\necho "Hello"\n'

    def _lua(self) -> str:
        return 'print("Hello")\n'

    def _swift(self) -> str:
        return 'import Foundation\n\nstruct Greeting {\n    let name: String\n    let age: Int\n    \n    func message() -> String {\n        return "Hello, \\(name)! You are \\(age) years old."\n    }\n}\n\nlet g = Greeting(name: "World", age: 25)\nprint(g.message())\n'

    def _go(self) -> str:
        return 'package main\n\nimport "fmt"\n\nfunc main() {\n    fmt.Println("Hello")\n}\n'

    def _rs(self) -> str:
        return 'fn main() {\n    println!("Hello");\n}\n'

    def _c(self) -> str:
        return '#include <stdio.h>\n\nint main(void) {\n    printf("Hello\\n");\n    return 0;\n}\n'

    def _cpp(self) -> str:
        return '#include <iostream>\n\nint main() {\n    std::cout << "Hello" << std::endl;\n    return 0;\n}\n'

    def _h(self) -> str:
        return "#ifndef SAMPLE_H\n#define SAMPLE_H\nvoid hello(void);\n#endif\n"

    def _hpp(self) -> str:
        return "#ifndef SAMPLE_HPP\n#define SAMPLE_HPP\nvoid hello();\n#endif\n"

    def _cs(self) -> str:
        return 'using System;\nclass Program {\n    static void Main() {\n        Console.WriteLine("Hello");\n    }\n}\n'

    def _objc(self) -> str:
        return '#import <Foundation/Foundation.h>\n\nint main() {\n    @autoreleasepool {\n        NSLog(@"Hello");\n    }\n    return 0;\n}\n'

    def _fortran(self) -> str:
        return "program hello\n    print *, 'Hello'\nend program hello\n"

    def _verilog(self) -> str:
        return 'module hello;\n  initial begin\n    $display("Hello");\n    $finish;\n  end\nendmodule\n'

    def _vhdl(self) -> str:
        return 'entity hello is\nend entity hello;\n\narchitecture behavioral of hello is\nbegin\n  process\n  begin\n    report "Hello";\n    wait;\n  end process;\nend architecture behavioral;\n'

    def _sql(self) -> str:
        return "CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);\nINSERT INTO users (name) VALUES ('Alice');\n"

    def _perl(self) -> str:
        return '#!/usr/bin/perl\nuse strict;\nuse warnings;\nprint "Hello\\n";\n'

    def _prolog(self) -> str:
        return "hello :- write('Hello'), nl.\n"

    def _pascal(self) -> str:
        return "program Hello;\nbegin\n  writeln('Hello');\nend.\n"

    def _julia(self) -> str:
        return 'function main()\n    println("Hello")\nend\n\nmain()\n'

    def _r(self) -> str:
        return 'hello <- function() {\n  print("Hello")\n}\n\nhello()\n'

    def _dart(self) -> str:
        return "void main() {\n  print('Hello');\n}\n"

    def _elixir(self) -> str:
        return 'defmodule Sample do\n  def hello do\n    IO.puts("Hello")\n  end\nend\n\nSample.hello()\n'

    def _erlang(self) -> str:
        return '-module(sample).\n-export([hello/0]).\n\nhello() ->\n    io:format("Hello~n").\n'

    def _erlang_hrl(self) -> str:
        return "-record(state, {name :: string(), value :: integer()}).\n"

    def _haskell(self) -> str:
        return 'module Main where\n\nmain :: IO ()\nmain = putStrLn "Hello"\n'

    def _haskell_lhs(self) -> str:
        return '> main :: IO ()\n> main = putStrLn "Hello"\n'

    def _ocaml(self) -> str:
        return 'let () =\n  print_endline "Hello"\n'

    def _ocaml_mli(self) -> str:
        return "val hello : unit -> unit\n"

    def _lisp(self) -> str:
        return '(defun hello ()\n  (format t "Hello~%"))\n\n(hello)\n'

    def _scheme(self) -> str:
        return '(define (hello)\n  (display "Hello")\n  (newline))\n\n(hello)\n'

    def _coffee(self) -> str:
        return 'greet = (name) ->\n  console.log "Hello, #{name}!"\n\ngreet "World"\n'

    def _solidity(self) -> str:
        return 'pragma solidity ^0.8.0;\n\ncontract Hello {\n    function greet() public pure returns (string memory) {\n        return "Hello";\n    }\n}\n'

    def _yara(self) -> str:
        return 'rule Hello {\n    strings:\n        $g = "Hello"\n    condition:\n        $g\n}\n'

    def _hcl(self) -> str:
        return 'resource "null_resource" "example" {\n  triggers = {\n    message = "Hello"\n  }\n}\n'

    def _proto(self) -> str:
        return 'syntax = "proto3";\n\nmessage User {\n  int32 id = 1;\n  string name = 2;\n}\n'

    def _textproto(self) -> str:
        return (
            "# proto-file: sample.proto\n"
            'name: "sample"\n'
            "id: 12345\n"
            "is_enabled: true\n"
            "settings {\n"
            "  timeout_seconds: 30\n"
            "  retry_count: 3\n"
            "}\n"
            'items: ["item1", "item2"]\n'
        )

    def _cmake(self) -> str:
        return "cmake_minimum_required(VERSION 3.10)\nproject(Sample)\nadd_executable(sample main.c)\n"

    def _gradle(self) -> str:
        return 'plugins {\n    id "java"\n}\n\nrepositories {\n    mavenCentral()\n}\n'

    def _groovy(self) -> str:
        return 'class Sample {\n    static void main(String[] args) {\n        println "Hello"\n    }\n}\n'

    def _bzl(self) -> str:
        return 'def hello_library():\n    native.genrule(\n        name = "hello",\n        outs = ["hello.txt"],\n        cmd = "echo Hello > $@",\n    )\n'

    def _gemspec(self) -> str:
        return 'Gem::Specification.new do |spec|\n  spec.name = "sample"\n  spec.version = "1.0.0"\nend\n'

    def _autoit(self) -> str:
        return 'MsgBox(0, "Hello", "Hello")\n'

    def _awk(self) -> str:
        return 'BEGIN {\n    print "Hello"\n}\n'

    def _handlebars(self) -> str:
        return "{{!-- Sample --}}\n<html><body><h1>{{message}}</h1></body></html>\n"

    def _jinja(self) -> str:
        return (
            '{% extends "base.html" %}\n'
            '{% block title %}{{ page_title | default("Home") }}{% endblock %}\n'
            "{% block content %}\n"
            "<h1>{{ user.name | upper }}</h1>\n"
            "{% for item in items if item.active %}\n"
            "  <li>{{ loop.index }}: {{ item.name | escape }}</li>\n"
            "{% else %}\n"
            "  <li>No items found</li>\n"
            "{% endfor %}\n"
            "{% endblock %}\n"
        )

    def _scss(self) -> str:
        return "$primary: #333;\n\nbody {\n  color: $primary;\n}\n"

    def _odin(self) -> str:
        return 'package main\n\nimport "core:fmt"\n\nmain :: proc() {\n    fmt.println("Hello")\n}\n'

    def _gleam(self) -> str:
        return 'import gleam/io\n\npub fn main() {\n  io.println("Hello")\n}\n'

    def _ipynb(self) -> str:
        return '{\n "cells": [{"cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], "source": ["print(\\"Hello\\")"]}],\n "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}},\n "nbformat": 4,\n "nbformat_minor": 4\n}\n'

    def _tcl(self) -> str:
        return 'puts "Hello"\n'

    def _m4(self) -> str:
        return "dnl Sample M4\ndefine(`GREETING', `Hello')dnl\nGREETING\n"

    def _brainfuck(self) -> str:
        return (
            "++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.\n"
        )

    def _smali(self) -> str:
        return ".class public LHello;\n.super Ljava/lang/Object;\n\n.method public static main([Ljava/lang/String;)V\n    .registers 2\n    return-void\n.end method\n"

    def _abnf(self) -> str:
        return '; Sample ABNF\nhello = "Hello" CRLF\n'

    def _aidl(self) -> str:
        return "interface IHello {\n    String greet(String name);\n}\n"

    def _gpx(self) -> str:
        return '<?xml version="1.0"?><gpx version="1.1" creator="Sample"><wpt lat="37.7749" lon="-122.4194"><name>Sample</name></wpt></gpx>\n'

    def _xsd(self) -> str:
        return '<?xml version="1.0"?><xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema"><xs:element name="sample" type="xs:string"/></xs:schema>\n'

    def _html(self) -> str:
        return "<!DOCTYPE html>\n<html><head><title>Sample</title></head><body><h1>Hello</h1></body></html>\n"

    def _tsv(self) -> str:
        return "id\tname\n1\tAlice\n2\tBob\n"

    def _jsonld(self) -> str:
        return '{\n  "@context": "https://json-ld.org/contexts/person.jsonld",\n  "@id": "http://example.org/sample",\n  "name": "Sample"\n}\n'

    def _yaml(self) -> str:
        return "name: sample\nversion: 1.0.0\n"

    def _asm(self) -> str:
        return "    .globl main\nmain:\n    pushq %rbp\n    movq %rsp, %rbp\n    movl $0, %eax\n    popq %rbp\n    ret\n"

    def _cobol(self) -> str:
        return "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY 'Hello'.\n           STOP RUN.\n"

    def _css(self) -> str:
        return (
            "body {\n    margin: 0;\n    padding: 0;\n    font-family: sans-serif;\n}\n"
        )

    def _json(self) -> str:
        return '{\n    "name": "sample",\n    "version": "1.0.0",\n    "description": "Sample JSON"\n}\n'

    def _jsonl(self) -> str:
        return '{"id": 1, "name": "Alice"}\n{"id": 2, "name": "Bob"}\n'

    def _svg(self) -> str:
        return '<?xml version="1.0"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">\n  <circle cx="50" cy="50" r="40" fill="red"/>\n</svg>\n'

    def _yaml(self) -> str:
        return "name: sample\nversion: 1.0.0\ndescription: Sample YAML\n"

    def _toml(self) -> str:
        return '[project]\nname = "sample"\nversion = "1.0.0"\ndescription = "Sample TOML"\n'

    def _ini(self) -> str:
        return "[section]\nkey = value\ncount = 42\n"

    def _dockerfile(self) -> str:
        return 'FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD ["python", "main.py"]\n'

    def _makefile(self) -> str:
        return ".PHONY: all clean\n\nall: build\n\nbuild:\n\tgcc -o main main.c\n\nclean:\n\trm -f main\n"

    def _bat(self) -> str:
        return "@echo off\necho Hello\npause\n"

    def _ps1(self) -> str:
        return 'Write-Host "Hello"\n'

    def _ahk(self) -> str:
        return "#NoEnv\n#SingleInstance Force\nSendMode Input\nMsgBox Hello from AutoHotkey\n"

    def _vbs(self) -> str:
        return 'MsgBox "Hello"\n'

    def _ksh(self) -> str:
        return '#!/bin/ksh\necho "Hello"\n'

    def _erb(self) -> str:
        return "<html>\n<body>\n<h1><%= @title %></h1>\n<% @items.each do |item| %>\n  <p><%= item %></p>\n<% end %>\n</body>\n</html>\n"

    def _vue(self) -> str:
        return '<template>\n  <div>{{ message }}</div>\n</template>\n\n<script setup>\nimport { ref } from "vue"\nconst message = ref("Hello")\n</script>\n\n<style scoped>\ndiv { color: blue; }\n</style>\n'

    def _clj(self) -> str:
        return '(ns sample.core)\n\n(defn hello [name]\n  (str "Hello, " name "!"))\n\n(println (hello "World"))\n'

    def _litcoffee(self) -> str:
        return 'Literate CoffeeScript\n=====================\n\nThis is a literate CoffeeScript file.\n\n    greet = (name) -> console.log "Hello, #{name}!"\n    greet "World"\n'

    def _elm(self) -> str:
        return 'module Main exposing (..)\n\nimport Html exposing (text)\n\nmain = text "Hello"\n'

    def _nix(self) -> str:
        return '{ pkgs ? import <nixpkgs> {} }:\n\npkgs.stdenv.mkDerivation {\n  name = "sample";\n  src = ./.;\n}\n'

    def _tf(self) -> str:
        return 'provider "aws" {\n  region = "us-east-1"\n}\n\nresource "aws_instance" "example" {\n  ami           = "ami-12345678"\n  instance_type = "t2.micro"\n}\n'

    def _vim(self) -> str:
        return '" Sample Vim script\nfunction! Hello()\n  echo "Hello"\nendfunction\n\ncmd! Hello call Hello()\n'

    def _aff(self) -> str:
        return "SET UTF-8\nFLAG num\nPFX A Y 1\nPFX A 0 re .\n"

    def _zig(self) -> str:
        return 'const std = @import("std");\n\npub fn main() void {\n    std.debug.print("Hello\\n", .{});\n}\n'

    def _csproj(self) -> str:
        return '<Project Sdk="Microsoft.NET.Sdk">\n  <PropertyGroup>\n    <OutputType>Exe</OutputType>\n    <TargetFramework>net8.0</TargetFramework>\n  </PropertyGroup>\n</Project>\n'

    def _vcxproj(self) -> str:
        return '<?xml version="1.0"?>\n<Project DefaultTargets="Build" ToolsVersion="17.0" xmlns="http://schemas.microsoft.com/developer/msbuild/2003">\n  <ItemGroup>\n    <ClCompile Include="main.cpp"/>\n  </ItemGroup>\n</Project>\n'

    def _hta(self) -> str:
        return '<html>\n<head>\n<hta:application id="sample" applicationname="Sample"/>\n</head>\n<body>\n<script language="VBScript">\nMsgBox "Hello"\n</script>\n</body>\n</html>\n'

    def _jnlp(self) -> str:
        return '<?xml version="1.0"?>\n<jnlp spec="1.0+" codebase="http://example.com/" href="sample.jnlp">\n  <information>\n    <title>Sample</title>\n    <vendor>Sample</vendor>\n  </information>\n  <resources>\n    <j2se version="1.8+"/>\n    <jar href="sample.jar"/>\n  </resources>\n  <application-desc main-class="Main"/>\n</jnlp>\n'

    def _twig(self) -> str:
        return "{% extends 'base.html.twig' %}\n\n{% block body %}\n  <h1>{{ title }}</h1>\n  {% for item in items %}\n    <p>{{ item }}</p>\n  {% endfor %}\n{% endblock %}\n"

    def _vba(self) -> str:
        return 'Sub Hello()\n    MsgBox "Hello"\nEnd Sub\n'

    def _mht(self) -> str:
        return 'From: <Saved by Browser>\nSubject: Sample\nDate: Mon, 1 Jan 2024 00:00:00 +0000\nMIME-Version: 1.0\nContent-Type: multipart/related;\n\ttype="text/html";\n\tboundary="----=_NextPart"\n\n------=_NextPart\nContent-Type: text/html; charset="utf-8"\n\n<html><body><h1>Hello</h1></body></html>\n------=_NextPart--\n'

    def _raku(self) -> str:
        return 'use v6;\n\nsub MAIN() {\n    say "Hello";\n}\n'

    def _cabal(self) -> str:
        return "cabal-version: 3.0\nname: sample\nversion: 1.0.0\nexecutable sample\n  main-is: Main.hs\n  build-depends: base >=4.14\n"

    def _dhall(self) -> str:
        return '{ name : Text, version : Natural }\n{ name = "sample", version = 1 }\n'

    def _purs(self) -> str:
        return 'module Main where\n\nimport Effect.Console (log)\n\nmain :: Effect Unit\nmain = log "Hello"\n'

    def _agda(self) -> str:
        return 'module Main where\n\nopen import IO\n\nmain = run (putStrLn "Hello")\n'

    def _idr(self) -> str:
        return 'module Main\n\nmain : IO ()\nmain = putStrLn "Hello"\n'

    def _lean(self) -> str:
        return 'def main : IO Unit :=\n  IO.println "Hello"\n'

    def _roc(self) -> str:
        return 'app "sample"\n    packages { pf: "https://github.com/roc-lang/basic-cli/releases/download/0.10.0/vKjCoDzYFP.zip" }\n    imports [pf.Stdout]\n    provides [main] to pf\n\nmain = Stdout.line "Hello"\n'

    def _mojo(self) -> str:
        return "def main() raises:\n    print('Hello')\n"

    def _carbon(self) -> str:
        return 'package Sample api;\n\nfn Main() -> i32 {\n    Print("Hello");\n    return 0;\n}\n'

    def _move(self) -> str:
        return 'module sample::hello {\n    public fun greet(): String {\n        string::utf8(b"Hello")\n    }\n}\n'

    def _cairo(self) -> str:
        return "#[contract]\nmod Hello {\n    #[abi(embed_v0)]\n    impl HelloImpl of IHello<ContractState> {\n        fn greet(self: @ContractState) -> felt252 {\n            'Hello'\n        }\n    }\n}\n"

    def _wgsl(self) -> str:
        return "@compute @workgroup_size(1)\nfn main() {\n}\n"

    def _glsl(self) -> str:
        return "#version 460\nvoid main() {\n    gl_FragColor = vec4(1.0, 0.0, 0.0, 1.0);\n}\n"

    def _hlsl(self) -> str:
        return "float4 main(float4 pos : SV_POSITION) : SV_TARGET {\n    return float4(1.0, 0.0, 0.0, 1.0);\n}\n"

    def _metal(self) -> str:
        return "#include <metal_stdlib>\nusing namespace metal;\n\nfragment float4 fragment_main() {\n    return float4(1.0, 0.0, 0.0, 1.0);\n}\n"

    def _spv(self) -> str:
        return "SpvMagic: 0x07230203\nVersion: 0x00010000\n"

    def _mlir(self) -> str:
        return "module {\n  func.func @main() {\n    return\n  }\n}\n"

    def _firrtl(self) -> str:
        return "circuit Sample :\n  module Sample :\n    input clock : Clock\n    input reset : UInt<1>\n"

    def _chisel(self) -> str:
        return "import chisel3._\n\nclass Sample extends Module {\n  val io = IO(new Bundle {})\n}\n"

    def _bluespec(self) -> str:
        return "package Sample;\ninterface Ifc;\n   method Action hello();\nendinterface\nendpackage\n"

    def _vb(self) -> str:
        return 'Module Module1\n    Sub Main()\n        Console.WriteLine("Hello, World!")\n    End Sub\nEnd Module\n'

    def _vbe(self) -> str:
        return 'Module Module1\n    Sub Main()\n        Console.WriteLine("Hello, World!")\n    End Sub\nEnd Module\n'

    def _asp(self) -> str:
        return '<%\nResponse.Write("Hello, World!")\n%>\n'

    def _aspx(self) -> str:
        return '<%@ Page Language="C#" %>\n<!DOCTYPE html>\n<html><body><h1>Hello</h1></body></html>\n'

    def _matlab(self) -> str:
        return "function result = hello()\n    result = 'Hello, World!';\nend\n"

    def _cljr(self) -> str:
        return '(ns sample.core)\n\n(defn greet [name]\n  (str "Hello, " name "!"))\n\n(println (greet "World"))\n'

    def _cljs(self) -> str:
        return '(ns sample.core)\n\n(defn greet [name]\n  (str "Hello, " name "!"))\n\n(println (greet "World"))\n'

    def _cobol_upper(self) -> str:
        return "       IDENTIFICATION DIVISION.\n       PROGRAM-ID. HELLO.\n       PROCEDURE DIVISION.\n           DISPLAY 'Hello'.\n           STOP RUN.\n"

    def _cobol_copy_upper(self) -> str:
        return "       01 SAMPLE-REC.\n           05 NAME PIC X(20).\n           05 AGE PIC 9(3).\n"

    def _prolog_upper(self) -> str:
        return "hello :- write('Hello'), nl.\n"

    def _algol68(self) -> str:
        return 'BEGIN\n    print(("Hello, World!", newl))\nEND\n'

    def _r_lower(self) -> str:
        return 'hello <- function() {\n  print("Hello")\n}\n\nhello()\n'

    def _po(self) -> str:
        return '# Sample PO file\nmsgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "Hello, World!"\nmsgstr "Hello, World!"\n'

    def _pot(self) -> str:
        return '# Sample PO template file\nmsgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n\nmsgid "Hello, World!"\nmsgstr ""\n'

    def _csv(self) -> str:
        return "id,name,email\n1,Alice,alice@example.com\n2,Bob,bob@example.com\n"

    def _xml(self) -> str:
        return '<?xml version="1.0" encoding="UTF-8"?>\n<root>\n  <item id="1">Sample</item>\n</root>\n'

    def _create_ps1(self) -> bytes:
        return b"""# PowerShell sample script
function Get-Greeting {
    param([string]$Name = "World")
    Write-Output "Hello, $Name!"
}

$items = Get-ChildItem -Path . -Filter *.txt
foreach ($item in $items) {
    Write-Host "Found file: $($item.FullName)"
}
"""
