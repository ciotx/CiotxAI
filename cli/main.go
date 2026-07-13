package main

import (
	"fmt"
	"os"

	"github.com/ciotx/cli/cmd"
)

func main() {
	if err := cmd.Execute(); err != nil {
		fmt.Fprintf(os.Stderr, "ciotx: %v\n", err)
		os.Exit(1)
	}
}
