"""DEPRECATED: This monolithic fixture generator is no longer the canonical path.

Use ``scripts/generators`` instead:

    rye run python -m scripts.generators --all --sources

This module is kept for reference only and will be removed in a future release.
All new fixture generation should go through the modular generator system in
``scripts/generators/``.

---

Generate sample fixture files for coverage testing.

This script creates minimal valid files for every format that can be
programmatically generated. Complex binary formats (Office, video, etc.)
are skipped and should be added manually.

Usage:
    python scripts/generate_fixtures.py [--force]
"""

import argparse
import struct
import tarfile
import zipfile
from io import BytesIO
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent.parent / "tests" / "fixtures"


def write_fixture(name: str, content: bytes | str, force: bool = False):
    """Write a fixture file, skipping existing ones unless force=True.

    Parameters
    ----------
    name : str
        Filename (e.g., ``'sample.png'``).
    content : bytes | str
        File content.
    force : bool
        Overwrite existing files.
    """
    path = FIXTURES_DIR / name
    if path.exists() and not force:
        return
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    print(f"  Created {name}")


# =============================================================================
# Text / Code Fixtures
# =============================================================================

CODE_SAMPLES = {
    "sample.py": '''#!/usr/bin/env python3
"""Sample Python file."""

def main():
    print("Hello, World!")

if __name__ == "__main__":
    main()
''',
    "sample.js": """// Sample JavaScript file
"use strict";

function main() {
    console.log("Hello, World!");
}

main();
""",
    "sample.ts": """// Sample TypeScript file
interface Greeting {
    name: string;
}

function greet({ name }: Greeting): string {
    return `Hello, ${name}!`;
}

console.log(greet({ name: "World" }));
""",
    "sample.go": """// Sample Go file
package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}
""",
    "sample.rs": """// Sample Rust file
fn main() {
    println!("Hello, World!");
}
""",
    "sample.java": """// Sample Java file
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
""",
    "sample.rb": """# Sample Ruby file
def main
  puts "Hello, World!"
end

main
""",
    "sample.php": """<?php
// Sample PHP file
echo "Hello, World!\\n";
?>
""",
    "sample.sh": """#!/bin/bash
# Sample shell script
echo "Hello, World!"
""",
    "sample.lua": """-- Sample Lua file
print("Hello, World!")
""",
    "sample.swift": """// Sample Swift file
print("Hello, World!")
""",
    "sample.kt": """// Sample Kotlin file
fun main() {
    println("Hello, World!")
}
""",
    "sample.scala": """// Sample Scala file
@main def main(): Unit =
  println("Hello, World!")
""",
    "sample.c": """/* Sample C file */
#include <stdio.h>

int main(void) {
    printf("Hello, World!\\n");
    return 0;
}
""",
    "sample.cpp": """// Sample C++ file
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
""",
    "sample.h": """/* Sample C header file */
#ifndef SAMPLE_H
#define SAMPLE_H

void hello(void);

#endif /* SAMPLE_H */
""",
    "sample.css": """/* Sample CSS file */
body {
    font-family: sans-serif;
    margin: 0;
    padding: 0;
}
""",
    "sample.html": """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Sample</title>
</head>
<body>
    <h1>Hello, World!</h1>
</body>
</html>
""",
    "sample.yaml": """# Sample YAML file
name: sample
version: 1.0.0
description: A sample YAML file
settings:
  debug: false
  log_level: info
""",
    "sample.toml": """# Sample TOML file
[package]
name = "sample"
version = "1.0.0"

[dependencies]
requests = ">=2.0"
""",
    "sample.ini": """; Sample INI file
[general]
name = sample
version = 1.0.0

[logging]
level = info
file = /var/log/sample.log
""",
    "sample.sql": """-- Sample SQL file
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT UNIQUE
);

INSERT INTO users (name, email) VALUES ('Alice', 'alice@example.com');
""",
    "sample.dart": """// Sample Dart file
void main() {
  print('Hello, World!');
}
""",
    "sample.zig": """// Sample Zig file
const std = @import("std");

pub fn main() void {
    std.debug.print("Hello, World!\\n", .{});
}
""",
    "sample.elm": """-- Sample Elm file
module Main exposing (main)

import Html exposing (text)

main =
    text "Hello, World!"
""",
    "sample.ex": """# Sample Elixir file
defmodule Sample do
  def hello do
    IO.puts("Hello, World!")
  end
end

Sample.hello()
""",
    "sample.erl": """%% Sample Erlang file
-module(sample).
-export([hello/0]).

hello() ->
    io:format("Hello, World!~n").
""",
    "sample.hs": """-- Sample Haskell file
module Main where

main :: IO ()
main = putStrLn "Hello, World!"
""",
    "sample.lisp": """;; Sample Lisp file
(defun hello ()
  (format t "Hello, World!~%"))

(hello)
""",
    "sample.ml": """(* Sample OCaml file *)
let () =
  print_endline "Hello, World!"
""",
    "sample.pl": """#!/usr/bin/perl
# Sample Perl file
use strict;
use warnings;

print "Hello, World!\\n";
""",
    "sample.proto": """// Sample Protocol Buffers file
syntax = "proto3";

message User {
  int32 id = 1;
  string name = 2;
  string email = 3;
}
""",
    "sample.r": """# Sample R file
hello <- function() {
  print("Hello, World!")
}

hello()
""",
    "sample.tf": """# Sample Terraform file
terraform {
  required_version = ">= 1.0"
}

resource "null_resource" "example" {
  triggers = {
    message = "Hello, World!"
  }
}
""",
    "sample.vim": """" Sample Vim script file
function! Hello()
  echo "Hello, World!"
endfunction

call Hello()
""",
    "sample.vue": """<!-- Sample Vue file -->
<template>
  <div>{{ message }}</div>
</template>

<script setup>
const message = "Hello, World!"
</script>
""",
    "sample.asm": """; Sample x86 assembly file (Linux)
section .data
    msg db "Hello, World!", 0

section .text
    global _start
_start:
    mov eax, 60
    xor edi, edi
    syscall
""",
    "sample.bat": """@echo off
REM Sample Windows batch file
echo Hello, World!
""",
    "sample.cmake": """# Sample CMake file
cmake_minimum_required(VERSION 3.10)
project(Sample)

add_executable(sample main.c)
""",
    "sample.gradle": """// Sample Gradle file
plugins {
    id "java"
}

repositories {
    mavenCentral()
}

dependencies {
    testImplementation "junit:junit:4.13"
}
""",
    "sample.groovy": """// Sample Groovy file
class Sample {
    static void main(String[] args) {
        println "Hello, World!"
    }
}
""",
    "sample.dockerfile": """# Sample Dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
CMD ["python", "main.py"]
""",
    "sample.makefile": """# Sample Makefile
.PHONY: all clean

all: build

build:
\t@echo "Building..."

clean:
\t@echo "Cleaning..."
""",
    "sample.nix": """# Sample Nix file
{ pkgs ? import <nixpkgs> {} }:

pkgs.stdenv.mkDerivation {
  name = "sample";
  src = ./.;
}
""",
    "sample.ps1": """# Sample PowerShell file
Write-Host "Hello, World!"
""",
    "sample.srt": """1
00:00:01,000 --> 00:00:04,000
Hello, World!

2
00:00:05,000 --> 00:00:08,000
This is a sample subtitle file.
""",
    "sample.vtt": """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, World!

00:00:05.000 --> 00:00:08.000
This is a sample WebVTT file.
""",
    "sample.rust": """// Sample Rust file (duplicate of .rs for coverage)
fn main() {
    println!("Hello, World!");
}
""",
    "sample.tsx": """// Sample TSX file
import React from "react";

export const App: React.FC = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.jsx": """// Sample JSX file
import React from "react";

export const App = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.jsonl": """{"id": 1, "name": "Alice"}
{"id": 2, "name": "Bob"}
{"id": 3, "name": "Charlie"}
""",
    "sample.rst": """Sample reStructuredText
=====================

This is a sample **reStructuredText** file.

- Item 1
- Item 2
- Item 3
""",
    "sample.diff": """--- a/original.txt
+++ b/modified.txt
@@ -1,3 +1,3 @@
-Hello
+Hello, World!
 This is a sample
-diff file
+diff file for testing
""",
    "sample.pot": """# Sample PO template file
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello, World!"
msgstr ""
""",
    "sample.ksh": """#!/bin/ksh
# Sample KornShell script
echo "Hello, World!"
""",
    "sample.text": """Hello, World!
This is a sample text file.
""",
    # Additional code languages
    "sample.coffee": """# Sample CoffeeScript file
greet = (name) ->
  console.log "Hello, #{name}!"

greet "World"
""",
    "sample.jl": """# Sample Julia file
function main()
    println("Hello, World!")
end

main()
""",
    "sample.scm": """;; Sample Scheme file
(define (hello)
  (display "Hello, World!")
  (newline))

(hello)
""",
    "sample.ss": """; Sample Scheme file (alternate extension)
(display "Hello, World!")
(newline)
""",
    "sample.pas": """{ Sample Pascal file }
program Hello;
begin
  writeln('Hello, World!');
end.
""",
    "sample.v": """// Sample Verilog file
module hello;
  initial begin
    $display("Hello, World!");
    $finish;
  end
endmodule
""",
    "sample.vhd": """-- Sample VHDL file
entity hello is
end entity hello;

architecture behavioral of hello is
begin
  process
  begin
    report "Hello, World!";
    wait;
  end process;
end architecture behavioral;
""",
    "sample.mli": """(* Sample OCaml interface file *)
val hello : unit -> unit
""",
    "sample.lhs": """> main :: IO ()
> main = putStrLn "Hello, World!"
""",
    "sample.erb": """<%# Sample ERB file %>
<html>
  <body>
    <h1><%= "Hello, World!" %></h1>
  </body>
</html>
""",
    "sample.gemspec": """# Sample Gemspec file
Gem::Specification.new do |spec|
  spec.name = "sample"
  spec.version = "1.0.0"
  spec.summary = "A sample gem"
end
""",
    "sample.bzl": """# Sample Bazel file
def hello_library():
    native.genrule(
        name = "hello",
        outs = ["hello.txt"],
        cmd = "echo 'Hello, World!' > $@",
    )
""",
    "sample.au3": """; Sample AutoIt file
MsgBox(0, "Hello", "Hello, World!")
""",
    "sample.awk": """# Sample AWK file
BEGIN {
    print "Hello, World!"
}
""",
    "sample.hbs": """{{!-- Sample Handlebars file --}}
<html>
  <body>
    <h1>{{message}}</h1>
  </body>
</html>
""",
    "sample.jinja": """{# Sample Jinja2 template #}
<html>
  <body>
    <h1>{{ message }}</h1>
  </body>
</html>
""",
    "sample.scss": """// Sample SCSS file
$primary-color: #333;

body {
  font-family: sans-serif;
  color: $primary-color;
}
""",
    "sample.sol": """// Sample Solidity file
pragma solidity ^0.8.0;

contract Hello {
    function greet() public pure returns (string memory) {
        return "Hello, World!";
    }
}
""",
    "sample.yar": """// Sample YARA rule
rule Hello {
    strings:
        $greeting = "Hello, World!"
    condition:
        $greeting
}
""",
    "sample.odin": """// Sample Odin file
package main

import "core:fmt"

main :: proc() {
    fmt.println("Hello, World!")
}
""",
    "sample.gleam": """// Sample Gleam file
import gleam/io

pub fn main() {
  io.println("Hello, World!")
}
""",
    "sample.ipynb": """{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": ["print(\\"Hello, World!\\")"]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 4
}
""",
    "sample.mjs": """// Sample ES Module JavaScript file
export function greet(name) {
    return `Hello, ${name}!`;
}
""",
    "sample.cjs": """// Sample CommonJS JavaScript file
function greet(name) {
    return `Hello, ${name}!`;
}

module.exports = { greet };
""",
    "sample.mts": """// Sample ES Module TypeScript file
export function greet(name: string): string {
    return `Hello, ${name}!`;
}
""",
    "sample.cts": """// Sample CommonJS TypeScript file
function greet(name: string): string {
    return `Hello, ${name}!`;
}

export = { greet };
""",
    "sample.pyi": """# Sample Python stub file
def greet(name: str) -> str: ...
""",
    "sample.hrl": """%% Sample Erlang header file
-record(state, {
    name :: string(),
    value :: integer()
}).
""",
    "sample.exs": """# Sample Elixir script file
IO.puts("Hello, World!")
""",
    "sample.clj": """;; Sample Clojure file
(defn hello []
  (println "Hello, World!"))

(hello)
""",
    "sample.kts": """// Sample Kotlin script file
fun main() {
    println("Hello, World!")
}

main()
""",
    "sample.cs": """// Sample C# file
using System;

class Program {
    static void Main() {
        Console.WriteLine("Hello, World!");
    }
}
""",
    "sample.vbs": """\' Sample VBScript file
MsgBox "Hello, World!"
""",
    "sample.tcl": """# Sample Tcl file
puts "Hello, World!"
""",
    "sample.m4": """dnl Sample M4 file
define(`GREETING', `Hello, World!')dnl
GREETING
""",
    "sample.bf": """++ Sample Brainfuck file
++++++++[>++++[>++>+++>+++>+<<<<-]>+>+>->>+[<]<-]>>.>---.+++++++..+++.>>.<-.<.+++.------.--------.>>+.>++.
""",
    "sample.pro": """% Sample Prolog file
hello :- write('Hello, World!'), nl.
""",
    "sample.smali": """# Sample Smali file
.class public LHello;
.super Ljava/lang/Object;

.method public static main([Ljava/lang/String;)V
    .registers 2
    sget-object v0, Ljava/lang/System;->out:Ljava/io/PrintStream;
    const-string v1, "Hello, World!"
    invoke-virtual {v0, v1}, Ljava/io/PrintStream;->println(Ljava/lang/String;)V
    return-void
.end method
""",
    "sample.textproto": """# Sample TextProto file
name: "sample"
version: 1
""",
    "sample.tsv": """id\tname\temail
1\tAlice\talice@example.com
2\tBob\tbob@example.com
""",
    "sample.asc": """-----BEGIN PGP SIGNATURE-----

iQEcBAEBAgAGBQJl7Z7aAAoJEHbK
-----END PGP SIGNATURE-----
""",
    "sample.bib": """@article{sample,
  author = {John Doe},
  title = {Sample Article},
  journal = {Sample Journal},
  year = {2024}
}
""",
    "sample.tex": """\\documentclass{article}
\\begin{document}
Hello, World!
\\end{document}
""",
    "sample.eml": """From: sender@example.com
To: recipient@example.com
Subject: Hello
Date: Mon, 1 Jan 2024 00:00:00 +0000
Content-Type: text/plain; charset="utf-8"

Hello, World!
""",
    "sample.patch": """--- a/original.txt
+++ b/modified.txt
@@ -1 +1 @@
-Hello
+Hello, World!
""",
    "sample.rdf": """<?xml version="1.0" encoding="UTF-8"?>
<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about="http://example.org/sample">
    <rdf:type rdf:resource="http://example.org/Type"/>
  </rdf:Description>
</rdf:RDF>
""",
    "sample.ics": """BEGIN:VCALENDAR
VERSION:2.0
PRODID:-//Sample//Sample//EN
BEGIN:VEVENT
DTSTART:20240101T000000Z
DTEND:20240101T010000Z
SUMMARY:Sample Event
END:VEVENT
END:VCALENDAR
""",
    "sample.m3u": """#EXTM3U
#EXTINF:60,Sample Track
sample.mp3
""",
    "sample.reg": """Windows Registry Editor Version 5.00

[HKEY_CURRENT_USER\\Software\\Sample]
"Name"="Sample"
""",
    "sample.plist": """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Name</key>
    <string>Sample</string>
</dict>
</plist>
""",
    "sample.lock": """# This file is automatically @generated.
# It is not intended for manual editing.
version = 3

[[package]]
name = "sample"
version = "1.0.0"
""",
    "sample.pem": """-----BEGIN CERTIFICATE-----
MIIBkTCB+wIJALRiMLAh0V3MMA0GCSqGSIb3DQEBCwUAMBExDzANBgNVBAMMBnNh
bXBsZTAeFw0yNDAxMDEwMDAwMDBaFw0yNTAxMDEwMDAwMDBaMBExDzANBgNVBAMM
-----END CERTIFICATE-----
""",
    "sample.pub": """ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC sample@host
""",
    "sample.torrent": """d8:announce35:http://tracker.example.com/announce7:comment15:Sample torrent13:creation datei1704067200e4:infod6:lengthi12e4:name8:hello.txtd12:piece lengthi32768e6:pieces20:abcdefghijklmnopqrst
""",
    "sample.vcard": """BEGIN:VCARD
VERSION:3.0
FN:Sample User
EMAIL:sample@example.com
END:VCARD
""",
    "sample.abnf": """; Sample ABNF file
hello = "Hello, World!" CRLF
""",
    "sample.aff": """SET UTF-8
TRY esianrtolcdugmphbyfvkwzESIANRTOLCDUGMPHBYFVKWZ
""",
    "sample.aidl": """// Sample AIDL file
interface IHello {
    String greet(String name);
}
""",
    "sample.gpx": """<?xml version="1.0" encoding="UTF-8"?>
<gpx version="1.1" creator="Sample">
  <wpt lat="37.7749" lon="-122.4194">
    <name>Sample Waypoint</name>
  </wpt>
</gpx>
""",
    "sample.xsd": """<?xml version="1.0" encoding="UTF-8"?>
<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema">
  <xs:element name="sample" type="xs:string"/>
</xs:schema>
""",
    "sample.htm": """<!DOCTYPE html>
<html>
<head><title>Sample</title></head>
<body><h1>Hello, World!</h1></body>
</html>
""",
    "sample.markdown": """# Sample Markdown

This is a **sample** Markdown file.

- Item 1
- Item 2
- Item 3
""",
    "sample.yml": """# Sample YAML file (alternate extension)
name: sample
version: 1.0.0
""",
    "sample.s": """# Sample x86 assembly file (AT&T syntax)
    .globl main
main:
    pushq %rbp
    movq %rsp, %rbp
    movl $0, %eax
    popq %rbp
    ret
""",
    "sample.cc": """// Sample C++ file (alternate extension)
#include <iostream>

int main() {
    std::cout << "Hello, World!" << std::endl;
    return 0;
}
""",
    "sample.hh": """// Sample C++ header file (alternate extension)
#ifndef SAMPLE_HH
#define SAMPLE_HH

void hello();

#endif
""",
    "sample.mm": """// Sample Objective-C file
#import <Foundation/Foundation.h>

int main() {
    @autoreleasepool {
        NSLog(@"Hello, World!");
    }
    return 0;
}
""",
    "sample.lsp": """;; Sample Lisp file (alternate extension)
(defun hello ()
  (format t "Hello, World!~%"))

(hello)
""",
    "sample.cl": """;; Sample OpenCL/Clojure file
__kernel void hello(__global float* output) {
    output[0] = 1.0f;
}
""",
    "sample.jsonld": """{
  "@context": "https://json-ld.org/contexts/person.jsonld",
  "@id": "http://example.org/sample",
  "name": "Sample Person"
}
""",
    "sample.j2": """{# Sample Jinja2 template (alternate extension) #}
<html>
  <body>
    <h1>{{ message }}</h1>
  </body>
</html>
""",
    "sample.handlebars": """{{!-- Sample Handlebars file (alternate extension) --}}
<html>
  <body>
    <h1>{{message}}</h1>
  </body>
</html>
""",
    "sample.mjsx": """// Sample TSX file with .mjsx extension
import React from "react";

export const App: React.FC = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.cjsx": """// Sample TSX file with .cjsx extension
import React from "react";

export const App: React.FC = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.mtsx": """// Sample TSX file with .mtsx extension
import React from "react";

export const App: React.FC = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.ctsx": """// Sample TSX file with .ctsx extension
import React from "react";

export const App: React.FC = () => {
    return <h1>Hello, World!</h1>;
};
""",
    "sample.webvtt": """WEBVTT

00:00:01.000 --> 00:00:04.000
Hello, World!

00:00:05.000 --> 00:00:08.000
This is a sample WebVTT file (alternate extension).
""",
    "sample.po": """# Sample PO file
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"

msgid "Hello, World!"
msgstr "Hello, World!"
""",
    "sample.url": """[InternetShortcut]
URL=https://example.com
""",
    "sample.aux": """\\relax
\\@writefile{toc}{\\contentsline {section}{\\numberline {1}Sample}{1}}
""",
    "sample.litcoffee": """Hello, World!
===========

This is a sample Literate CoffeeScript file.

    console.log "Hello, World!"
""",
}


# =============================================================================
# Minimal Binary Fixtures
# =============================================================================


def create_png():
    """Create a minimal valid 1x1 PNG file."""
    # 1x1 red pixel PNG
    import zlib

    def chunk(chunk_type, data):
        c = chunk_type + data
        return (
            struct.pack(">I", len(data))
            + c
            + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
        )

    sig = b"\x89PNG\r\n\x1a\n"
    ihdr = chunk(b"IHDR", struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0))
    raw = zlib.compress(b"\x00\xff\x00\x00")  # filter=0, R=255, G=0, B=0
    idat = chunk(b"IDAT", raw)
    iend = chunk(b"IEND", b"")
    return sig + ihdr + idat + iend


def create_gif():
    """Create a minimal valid 1x1 GIF file."""
    return (
        b"GIF89a"  # Header
        b"\x01\x00"  # Width: 1
        b"\x01\x00"  # Height: 1
        b"\x80\x00\x00"  # GCT flag, 2 colors
        b"\x00\x00\x00"  # Background, aspect
        b"\xff\x00\x00"  # Color 0: red
        b"\x00\x00\x00"  # Color 1: black
        b"\x2c"  # Image separator
        b"\x00\x00\x00\x00"  # Left, top
        b"\x01\x00\x01\x00"  # Width, height
        b"\x00"  # No local color table
        b"\x02"  # Min code size
        b"\x02"  # Block size
        b"\x4c\x01"  # Image data
        b"\x00"  # Block terminator
        b"\x3b"  # Trailer
    )


def create_bmp():
    """Create a minimal valid 1x1 BMP file."""
    return (
        b"BM"  # Signature
        + struct.pack("<I", 62)  # File size
        + struct.pack("<HH", 0, 0)  # Reserved
        + struct.pack("<I", 62)  # Pixel data offset
        + struct.pack("<I", 40)  # DIB header size
        + struct.pack("<i", 1)  # Width
        + struct.pack("<i", 1)  # Height
        + struct.pack("<HH", 1, 24)  # Planes, bits per pixel
        + struct.pack("<I", 0)  # Compression
        + struct.pack("<I", 0)  # Image size
        + struct.pack("<i", 2835)  # X pixels per meter
        + struct.pack("<i", 2835)  # Y pixels per meter
        + struct.pack("<I", 0)  # Colors used
        + struct.pack("<I", 0)  # Important colors
        + b"\xff\x00\x00\x00"  # Pixel data (BGR + padding)
    )


def create_ico():
    """Create a minimal valid ICO file (1x1)."""
    return (
        b"\x00\x00"  # Reserved
        + struct.pack("<H", 1)  # Type: 1 = ICO
        + struct.pack("<H", 1)  # Count: 1 image
        # Image entry
        + b"\x01"  # Width: 1
        + b"\x01"  # Height: 1
        + b"\x00"  # Color count
        + b"\x00"  # Reserved
        + struct.pack("<H", 1)  # Color planes
        + struct.pack("<H", 32)  # Bits per pixel
        + struct.pack("<I", 40 + 4)  # Data size
        + struct.pack("<I", 22)  # Data offset
        # BMP header (BITMAPINFOHEADER)
        + struct.pack("<I", 40)  # Header size
        + struct.pack("<i", 1)  # Width
        + struct.pack("<i", 2)  # Height (doubled for XOR mask)
        + struct.pack("<H", 1)  # Planes
        + struct.pack("<H", 32)  # Bits per pixel
        + struct.pack("<I", 0)  # Compression
        + struct.pack("<I", 0)  # Image size
        + struct.pack("<i", 0)  # X pixels per meter
        + struct.pack("<i", 0)  # Y pixels per meter
        + struct.pack("<I", 0)  # Colors used
        + struct.pack("<I", 0)  # Important colors
        # Pixel data (BGRA)
        + b"\xff\x00\x00\xff"  # Red pixel
        # AND mask (1 bit per pixel, padded to 4 bytes)
        + b"\x00\x00\x00\x00"
    )


def create_tiff():
    """Create a minimal valid TIFF file."""
    return (
        b"II"  # Little-endian
        + struct.pack("<H", 42)  # TIFF magic
        + struct.pack("<I", 8)  # Offset to first IFD
        # IFD
        + struct.pack("<H", 0)  # Number of entries
    )


def create_wav():
    """Create a minimal valid WAV file (1 sample, 8-bit mono)."""
    data = b"\x80"  # Single silence sample
    return (
        b"RIFF"
        + struct.pack("<I", 36 + len(data))  # File size - 8
        + b"WAVE"
        + b"fmt "
        + struct.pack("<I", 16)  # Subchunk size
        + struct.pack("<H", 1)  # PCM
        + struct.pack("<H", 1)  # Mono
        + struct.pack("<I", 8000)  # Sample rate
        + struct.pack("<I", 8000)  # Byte rate
        + struct.pack("<H", 1)  # Block align
        + struct.pack("<H", 8)  # Bits per sample
        + b"data"
        + struct.pack("<I", len(data))
        + data
    )


def create_midi():
    """Create a minimal valid MIDI file."""
    return (
        b"MThd"
        + struct.pack(">I", 6)  # Header chunk size
        + struct.pack(">HHH", 0, 1, 480)  # Format, tracks, division
        + b"MTrk"
        + struct.pack(">I", 4)  # Track chunk size
        + b"\x00\xff\x2f\x00"  # End of track meta-event
    )


def create_ogg():
    """Create a minimal valid OGG file."""
    # Minimal OGG page with BOS flag
    ogg_page = (
        b"OggS"  # Capture pattern
        + b"\x00"  # Version
        + b"\x02"  # Header type: BOS
        + struct.pack("<q", 0)  # Granule position
        + struct.pack("<I", 1)  # Serial number
        + struct.pack("<I", 0)  # Page sequence
        + struct.pack("<I", 0)  # CRC (placeholder)
        + b"\x01"  # Segments count
        + b"\x00"  # Segment table
    )
    return ogg_page


def create_webp():
    """Create a minimal valid WebP file (lossy)."""
    # Minimal VP8 chunk
    vp8_data = (
        b"\x9d\x01\x2a"  # VP8 signature
        + b"\x01\x00\x00"  # Start code
        + struct.pack("<H", 1)  # Width (1)
        + struct.pack("<H", 1)  # Height (1)
        + b"\x00"  # Rest of frame header
    )
    return (
        b"RIFF"
        + struct.pack("<I", 4 + 8 + len(vp8_data))  # File size
        + b"WEBP"
        + b"VP8 "
        + struct.pack("<I", len(vp8_data))
        + vp8_data
    )


def create_svg():
    """Create a minimal valid SVG file."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100">
  <rect width="100" height="100" fill="red"/>
</svg>
"""


def create_rtf():
    """Create a minimal valid RTF file."""
    return r"{\rtf1\ansi\deff0{\fonttbl{\f0 Times New Roman;}}Hello, World!}"


def create_epub():
    """Create a minimal valid EPUB file."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        # mimetype must be first and uncompressed
        zf.writestr(
            "mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED
        )
        zf.writestr(
            "META-INF/container.xml",
            """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>""",
        )
        zf.writestr(
            "OEBPS/content.opf",
            """<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="uid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="uid">urn:uuid:sample</dc:identifier>
    <dc:title>Sample EPUB</dc:title>
    <dc:language>en</dc:language>
  </metadata>
  <manifest>
    <item id="ch1" href="ch1.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine>
    <itemref idref="ch1"/>
  </spine>
</package>""",
        )
        zf.writestr(
            "OEBPS/ch1.xhtml",
            """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head><title>Sample</title></head>
<body><p>Hello, World!</p></body>
</html>""",
        )
    return buf.getvalue()


def create_tar():
    """Create a minimal valid tar archive."""
    buf = BytesIO()
    with tarfile.open(fileobj=buf, mode="w") as tf:
        data = b"Hello, World!\n"
        info = tarfile.TarInfo(name="hello.txt")
        info.size = len(data)
        tf.addfile(info, BytesIO(data))
    return buf.getvalue()


def create_gz():
    """Create a minimal valid gzip file."""
    import gzip

    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as f:
        f.write(b"Hello, World!\n")
    return buf.getvalue()


def create_bz2():
    """Create a minimal valid bzip2 file."""
    import bz2

    return bz2.compress(b"Hello, World!\n")


def create_xz():
    """Create a minimal valid xz file."""
    import lzma

    return lzma.compress(b"Hello, World!\n")


def create_zip():
    """Create a minimal valid ZIP file."""
    buf = BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("hello.txt", "Hello, World!\n")
    return buf.getvalue()


def create_jpeg():
    """Create a minimal valid JPEG file (1x1)."""
    return (
        b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00\x01\x00\x01\x00\x00"
        b"\xff\xdb\x00\x43\x00\x08\x06\x06\x07\x06\x05\x08\x07\x07\x07\x09\x09"
        b"\x08\x0a\x0c\x14\x0d\x0c\x0b\x0b\x0c\x19\x12\x13\x0f\x14\x1d\x1a\x1f"
        b"\x1e\x1d\x1a\x1c\x1c\x20\x24\x2e\x27\x20\x22\x2c\x23\x1c\x1c\x28\x37"
        b"\x29\x2c\x30\x31\x34\x34\x34\x1f\x27\x39\x3d\x38\x32\x3c\x2e\x33\x34"
        b"\x32\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xc4\x00"
        b"\x1f\x00\x00\x01\x05\x01\x01\x01\x01\x01\x01\x00\x00\x00\x00\x00\x00"
        b"\x00\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\xff\xc4\x00\xb5"
        b"\x10\x00\x02\x01\x03\x03\x02\x04\x03\x05\x05\x04\x04\x00\x00\x01\x7d"
        b"\x01\x02\x03\x00\x04\x11\x05\x12\x21\x31\x41\x06\x13\x51\x61\x07\x22"
        b"\x71\x14\x32\x81\x91\xa1\x08\x23\x42\xb1\xc1\x15\x52\xd1\xf0\x24\x33"
        b"\x62\x72\x82\x09\x0a\x16\x17\x18\x19\x1a\x25\x26\x27\x28\x29\x2a\x34"
        b"\x35\x36\x37\x38\x39\x3a\x43\x44\x45\x46\x47\x48\x49\x4a\x53\x54\x55"
        b"\x56\x57\x58\x59\x5a\x63\x64\x65\x66\x67\x68\x69\x6a\x73\x74\x75\x76"
        b"\x77\x78\x79\x7a\x83\x84\x85\x86\x87\x88\x89\x8a\x92\x93\x94\x95\x96"
        b"\x97\x98\x99\x9a\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xb2\xb3\xb4\xb5"
        b"\xb6\xb7\xb8\xb9\xba\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xd2\xd3\xd4"
        b"\xd5\xd6\xd7\xd8\xd9\xda\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xf1"
        b"\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xff\xda\x00\x08\x01\x01\x00\x00"
        b"\x3f\x00\x7b\x40\x03\xff\xd9"
    )


def create_ttf():
    """Create a minimal valid TTF file."""
    # Minimal TTF with required tables
    return (
        struct.pack(">I", 0x00010000)  # sfVersion
        + struct.pack(">H", 1)  # numTables
        + struct.pack(">H", 16)  # searchRange
        + struct.pack(">H", 0)  # entrySelector
        + struct.pack(">H", 16)  # rangeShift
        # 'head' table
        + b"head"  # tag
        + struct.pack(">I", 0x00000000)  # checkSum
        + struct.pack(">I", 12)  # offset
        + struct.pack(">I", 54)  # length
        # head table data (minimal)
        + struct.pack(">I", 0x00010000)  # version
        + struct.pack(">I", 0x00000000)  # fontRevision
        + struct.pack(">I", 0x00000000)  # checkSumAdjustment
        + struct.pack(">I", 0x5F0F3CF5)  # magicNumber
        + struct.pack(">H", 0x0000)  # flags
        + struct.pack(">H", 1000)  # unitsPerEm
        + struct.pack(">q", 0)  # created
        + struct.pack(">q", 0)  # modified
        + struct.pack(">h", 0)  # xMin
        + struct.pack(">h", 0)  # yMin
        + struct.pack(">h", 0)  # xMax
        + struct.pack(">h", 0)  # yMax
        + struct.pack(">H", 0)  # macStyle
        + struct.pack(">H", 1)  # lowestRecPPEM
        + struct.pack(">h", 2)  # fontDirectionHint
        + struct.pack(">h", 0)  # indexToLocFormat
        + struct.pack(">h", 0)  # glyphDataFormat
    )


def create_woff():
    """Create a minimal valid WOFF file."""
    # WOFF wraps TTF with a header
    ttf = create_ttf()
    return (
        b"wOFF"  # Signature
        + struct.pack(">I", 0x00010000)  # flavor
        + struct.pack(">I", 44 + len(ttf))  # length
        + struct.pack(">H", 1)  # numTables
        + struct.pack(">H", 0)  # reserved
        + struct.pack(">I", 44)  # totalSfntSize
        + struct.pack(">H", 0)  # majorVersion
        + struct.pack(">H", 0)  # minorVersion
        + struct.pack(">I", 0)  # metaOffset
        + struct.pack(">I", 0)  # metaLength
        + struct.pack(">I", 0)  # metaOrigLength
        + struct.pack(">I", 0)  # privOffset
        + struct.pack(">I", 0)  # privLength
        # Table directory entry
        + b"head"  # tag
        + struct.pack(">I", 44)  # offset
        + struct.pack(">I", len(ttf))  # compLength
        + struct.pack(">I", len(ttf))  # origLength
        + struct.pack(">I", 0)  # origChecksum
        + ttf
    )


def create_sqlite():
    """Create a minimal valid SQLite database file."""
    # SQLite header (100 bytes) + minimal page
    header = bytearray(100)
    header[0:16] = b"SQLite format 3\x00"
    struct.pack_into(">H", header, 16, 4096)  # Page size
    struct.pack_into(">B", header, 18, 1)  # File format write version
    struct.pack_into(">B", header, 19, 1)  # File format read version
    struct.pack_into(">B", header, 20, 0)  # Reserved space
    struct.pack_into(">B", header, 21, 64)  # Max embedded payload fraction
    struct.pack_into(">B", header, 22, 32)  # Min embedded payload fraction
    struct.pack_into(">B", header, 23, 32)  # Leaf payload fraction
    struct.pack_into(">I", header, 24, 1)  # File change counter
    struct.pack_into(">I", header, 28, 1)  # Database size in pages
    struct.pack_into(">I", header, 92, 4)  # Version-valid-for number
    struct.pack_into(">I", header, 96, 3008000)  # SQLite version number
    # First page: B-tree page header
    page = bytearray(4096)
    page[:100] = header
    page[100] = 0x0D  # Leaf table b-tree page
    return bytes(page)


BINARY_GENERATORS = {
    "sample.png": create_png,
    "sample.gif": create_gif,
    "sample.bmp": create_bmp,
    "sample.ico": create_ico,
    "sample.tiff": create_tiff,
    "sample.jpg": create_jpeg,
    "sample.jpeg": create_jpeg,
    "sample.svg": create_svg,
    "sample.webp": create_webp,
    "sample.wav": create_wav,
    "sample.mid": create_midi,
    "sample.midi": create_midi,
    "sample.ogg": create_ogg,
    "sample.rtf": create_rtf,
    "sample.epub": create_epub,
    "sample.tar": create_tar,
    "sample.gz": create_gz,
    "sample.bz2": create_bz2,
    "sample.xz": create_xz,
    "sample.zip": create_zip,
    "sample.ttf": create_ttf,
    "sample.woff": create_woff,
    "sample.sqlite": create_sqlite,
    # Additional binary formats
    "sample.tgz": lambda: create_gz(),  # Same as .gz
    "sample.tar.gz": lambda: create_gz(),  # Same as .gz
    "sample.tbz2": lambda: create_bz2(),  # Same as .bz2
    "sample.tar.bz2": lambda: create_bz2(),  # Same as .bz2
    "sample.xpi": create_zip,  # XPI is just a ZIP
    "sample.jar": create_zip,  # JAR is just a ZIP
    "sample.apk": create_zip,  # APK is just a ZIP
}


def main():
    """Generate all fixture files."""
    parser = argparse.ArgumentParser(description="Generate sample fixture files")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    print("=== Generating Text/Code Fixtures ===")
    count = 0
    for name, content in sorted(CODE_SAMPLES.items()):
        write_fixture(name, content, force=args.force)
        count += 1
    print(f"  Generated {count} text/code fixtures\n")

    print("=== Generating Binary Fixtures ===")
    count = 0
    for name, generator in sorted(BINARY_GENERATORS.items()):
        try:
            content = generator()
            write_fixture(name, content, force=args.force)
            count += 1
        except Exception as e:
            print(f"  FAILED {name}: {e}")
    print(f"  Generated {count} binary fixtures\n")

    # Summary
    existing = sorted(FIXTURES_DIR.glob("sample.*"))
    print(f"Total fixtures: {len(existing)}")
    for f in existing:
        print(f"  {f.name} ({f.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
