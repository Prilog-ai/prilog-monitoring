// Command go-obfuscate generates buildable SDK source while retaining its public API.
package main

import (
	"bytes"
	"flag"
	"fmt"
	"go/ast"
	"go/format"
	"go/parser"
	"go/token"
	"go/types"
	"os"
	"path/filepath"
	"sort"
	"strconv"
	"strings"

	"golang.org/x/tools/go/ast/astutil"
	"golang.org/x/tools/go/packages"
)

func main() {
	if err := run(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func run() error {
	source := flag.String("source", "", "readable SDK Go file outside the distribution repository")
	module := flag.String("module", "", "destination Go module directory")
	check := flag.Bool("check", false, "verify the existing artifact instead of writing it")
	flag.Parse()
	if *source == "" || *module == "" {
		return fmt.Errorf("usage: go-obfuscate -source /path/to/readable/prilog.go -module /path/to/golang [-check]")
	}
	sourcePath, err := filepath.EvalSymlinks(*source)
	if err != nil {
		return err
	}
	sourcePath, err = filepath.Abs(sourcePath)
	if err != nil {
		return err
	}
	moduleDir, err := filepath.EvalSymlinks(*module)
	if err != nil {
		return err
	}
	moduleDir, err = filepath.Abs(moduleDir)
	if err != nil {
		return err
	}
	relative, err := filepath.Rel(filepath.Dir(moduleDir), sourcePath)
	if err != nil {
		return err
	}
	if relative != ".." && !strings.HasPrefix(relative, ".."+string(filepath.Separator)) {
		return fmt.Errorf("readable SDK sources must be outside the distribution repository")
	}
	input, err := os.ReadFile(sourcePath)
	if err != nil {
		return err
	}
	target := filepath.Join(moduleDir, "prilog.go")
	loaded, err := packages.Load(&packages.Config{
		Dir: moduleDir, Mode: packages.LoadSyntax,
		BuildFlags: []string{"-mod=mod"},
		Env:        append(os.Environ(), "GOWORK=off"),
		Overlay:    map[string][]byte{target: input},
	}, ".")
	if err != nil {
		return err
	}
	if packages.PrintErrors(loaded) != 0 || len(loaded) != 1 || len(loaded[0].Syntax) != 1 {
		return fmt.Errorf("expected one successfully type-checked SDK implementation file")
	}
	pkg := loaded[0]
	file := pkg.Syntax[0]

	// Package imports, tags, and formatting directives retain their required syntax.
	reservedStrings := map[*ast.BasicLit]bool{}
	ast.Inspect(file, func(node ast.Node) bool {
		switch node := node.(type) {
		case *ast.ImportSpec:
			reservedStrings[node.Path] = true
		case *ast.Field:
			if node.Tag != nil {
				reservedStrings[node.Tag] = true
			}
		case *ast.CallExpr:
			selector, ok := node.Fun.(*ast.SelectorExpr)
			if !ok || len(node.Args) == 0 {
				break
			}
			object := pkg.TypesInfo.Uses[selector.Sel]
			if object != nil && object.Pkg() != nil && object.Pkg().Path() == "fmt" {
				if literal, ok := node.Args[0].(*ast.BasicLit); ok {
					reservedStrings[literal] = true
				}
			}
		}
		return true
	})

	objects := []types.Object{}
	seen := map[types.Object]bool{}
	identifiers := map[string]bool{}
	ast.Inspect(file, func(node ast.Node) bool {
		if identifier, ok := node.(*ast.Ident); ok {
			identifiers[identifier.Name] = true
		}
		return true
	})
	for _, object := range pkg.TypesInfo.Defs {
		if object == nil || object.Pkg() != pkg.Types || object.Exported() || object.Name() == "_" || seen[object] {
			continue
		}
		if _, imported := object.(*types.PkgName); imported {
			continue
		}
		if object.Name() == "init" {
			continue
		}
		seen[object] = true
		objects = append(objects, object)
	}
	sort.Slice(objects, func(i, j int) bool { return objects[i].Pos() < objects[j].Pos() })
	next := 0
	unique := func() string {
		for {
			next++
			name := fmt.Sprintf("_p%04x", next)
			if !identifiers[name] {
				identifiers[name] = true
				return name
			}
		}
	}
	renamed := map[types.Object]string{}
	for _, object := range objects {
		renamed[object] = unique()
	}
	for identifier, object := range pkg.TypesInfo.Defs {
		if name := renamed[object]; name != "" {
			identifier.Name = name
		}
	}
	for identifier, object := range pkg.TypesInfo.Uses {
		if name := renamed[object]; name != "" {
			identifier.Name = name
		}
	}

	tableName, decoderName := unique(), unique()
	values := []string{}
	indexes := map[string]int{}
	astutil.Apply(file, func(cursor *astutil.Cursor) bool {
		literal, ok := cursor.Node().(*ast.BasicLit)
		if !ok || literal.Kind != token.STRING || reservedStrings[literal] {
			return true
		}
		value, err := strconv.Unquote(literal.Value)
		if err != nil || value == "" {
			return true
		}
		index, exists := indexes[value]
		if !exists {
			index = len(values)
			indexes[value] = index
			values = append(values, value)
		}
		cursor.Replace(&ast.IndexExpr{X: ast.NewIdent(tableName), Index: &ast.BasicLit{Kind: token.INT, Value: fmt.Sprintf("0x%x", index)}})
		return false
	}, nil)
	file.Doc, file.Comments = nil, nil
	var helpers strings.Builder
	fmt.Fprintf(&helpers, "package %s\nvar %s = [...]string{\n", file.Name.Name, tableName)
	for _, value := range values {
		fmt.Fprintf(&helpers, "%s([]byte{", decoderName)
		for _, b := range []byte(value) {
			fmt.Fprintf(&helpers, "0x%02x,", b^0xa7)
		}
		helpers.WriteString("}),\n")
	}
	fmt.Fprintf(&helpers, "}\nfunc %s(v []byte) string { for i := range v { v[i] ^= 0xa7 }; return string(v) }\n", decoderName)
	generated, err := parser.ParseFile(pkg.Fset, "generated_strings.go", helpers.String(), 0)
	if err != nil {
		return err
	}
	file.Decls = append(file.Decls, generated.Decls...)
	var output bytes.Buffer
	output.WriteString("// Code generated by go-obfuscate; DO NOT EDIT.\n// Copyright (c) 2026 Prilog. MIT; see LICENSE.\n")
	if err := format.Node(&output, pkg.Fset, file); err != nil {
		return err
	}
	formatted, err := format.Source(output.Bytes())
	if err != nil {
		return err
	}
	if *check {
		current, err := os.ReadFile(target)
		if err != nil {
			return err
		}
		if !bytes.Equal(current, formatted) {
			return fmt.Errorf("Go runtime differs from the reproducible build")
		}
		fmt.Println("Verified golang/prilog.go")
		return nil
	}
	if err := os.WriteFile(target, formatted, 0644); err != nil {
		return err
	}
	fmt.Println("Generated golang/prilog.go")
	return nil
}
