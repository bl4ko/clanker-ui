package main

import (
	"bytes"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"regexp"
)

const stampPrefix = "/*! clanker-ui | "

var stampVersion = regexp.MustCompile(`^[0-9]+\.[0-9]+\.[0-9]+(-[0-9A-Za-z.-]+)?$`)

func stampMain(args []string) error {
	fset := flag.NewFlagSet("stamp", flag.ExitOnError)
	version := fset.String("version", "", "release version without the v, for example 0.3.0")
	fset.Parse(args)
	names, err := stamp(*version, fset.Args())
	if err != nil {
		return err
	}
	for _, n := range names {
		fmt.Println(n)
	}
	return nil
}

func stamp(version string, dirs []string) ([]string, error) {
	if !stampVersion.MatchString(version) {
		return nil, fmt.Errorf("stamp: version %q is not X.Y.Z", version)
	}
	if len(dirs) == 0 {
		return nil, errors.New("stamp: no directory")
	}
	files := map[string][]byte{}
	var names []string
	for _, dir := range dirs {
		matches, err := filepath.Glob(filepath.Join(dir, "clanker-ui*"))
		if err != nil {
			return nil, err
		}
		for _, f := range matches {
			if ext := filepath.Ext(f); ext != ".css" && ext != ".js" {
				continue
			}
			b, err := os.ReadFile(f)
			if err != nil {
				return nil, err
			}
			if !bytes.HasPrefix(b, []byte(stampPrefix)) {
				return nil, fmt.Errorf("stamp: %s does not start with %q", f, stampPrefix)
			}
			files[f] = append([]byte("/*! clanker-ui v"+version+" | "), b[len(stampPrefix):]...)
			names = append(names, f)
		}
	}
	if len(names) == 0 {
		return nil, fmt.Errorf("stamp: no clanker-ui*.css or clanker-ui*.js in %v", dirs)
	}
	for _, f := range names {
		if err := os.WriteFile(f, files[f], 0o644); err != nil {
			return nil, err
		}
	}
	return names, nil
}
