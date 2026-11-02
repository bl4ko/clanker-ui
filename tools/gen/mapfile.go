package main

import (
	"fmt"
	"os"
	"strings"
)

func readMap(path string) (map[string]string, map[string]string, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, nil, err
	}
	return parseMap(string(b))
}

func parseMap(text string) (map[string]string, map[string]string, error) {
	out, fps := map[string]string{}, map[string]string{}
	for i, line := range strings.Split(text, "\n") {
		if strings.TrimSpace(line) == "" {
			continue
		}
		cols := strings.Split(line, "\t")
		key := strings.TrimSpace(cols[0])
		if len(cols) < 2 || len(cols) > 3 || key == "" || strings.TrimSpace(cols[1]) == "" {
			return nil, nil, fmt.Errorf("map line %d: want <key><TAB><selector>[<TAB><fingerprint>]", i+1)
		}
		if _, dup := out[key]; dup {
			return nil, nil, fmt.Errorf("map line %d: %s twice", i+1, key)
		}
		out[key] = strings.TrimSpace(cols[1])
		if len(cols) == 3 {
			fps[key] = strings.TrimSpace(cols[2])
		}
		if strings.Contains(key, "#") && fps[key] == "" {
			return nil, nil, fmt.Errorf("map line %d: %s has #n and needs a class fingerprint in a third column", i+1, key)
		}
	}
	return out, fps, nil
}
