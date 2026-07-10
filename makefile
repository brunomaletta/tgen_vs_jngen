CXX ?= g++
CXXFLAGS = -std=c++17 -O2 -Wall
INCLUDES = -Ivendor/tgen/single_include -Ivendor/jngen

ifdef QUICK
CXXFLAGS += -DQUICK
endif

BENCH_BIN = build/benchmarks/run
VIZ_BIN = build/visualize/samples
BENCH_JSON = docs/benchmark_results.json
TGEN_DOC_BUILD = vendor/tgen/docs/build
TGEN_XML_INDEX = vendor/tgen/docs/build/xml/index.xml
# Doxygen 1.14 multithreading is flaky (SIGSEGV on CI); tgen Doxyfile uses 1 but its
# makefile overrides with NPROCS — keep doc passes single-threaded here.
TGEN_DOC_NPROCS ?= 1
DOC ?= docs/comparison.html
DOC_PATH := $(abspath $(DOC))

.DEFAULT_GOAL := help

.PHONY: all vendor benchmark visualize docs doc site opendoc check clean help

all: vendor benchmark visualize docs

help:
	@echo "Targets:"
	@echo "  vendor     - init submodules and build jngen.h"
	@echo "  benchmark  - run performance comparison → docs/benchmark_results.json"
	@echo "  visualize  - generate geometry sample SVGs"
	@echo "  docs       - regenerate comparison.html + bundled vendor docs"
	@echo "  check      - validate operations.yaml vs benchmark_results.json"
	@echo "  site       - docs + GitHub Pages bundle (gallery SVGs committed; no benchmark)"
	@echo "  doc        - alias for docs"
	@echo "  opendoc    - open comparison.html in Chrome"
	@echo "  all        - vendor + benchmark + visualize + docs"
	@echo "  clean      - remove build/ and results/"
	@echo ""
	@echo "Benchmarks run locally; commit docs/benchmark_results.json."
	@echo "CI/Pages consume benchmark_results.json and committed gallery SVGs."
	@echo "Regenerate gallery with 'make visualize', then commit docs/gallery/*.svg."
	@echo "Use QUICK=1 for n=1e5 instead of n=1e6 benchmarks."

vendor:
	git submodule update --init --recursive
	cd vendor/jngen && python3 build.py
	cd vendor/jngen && git restore jngen.h

$(BENCH_BIN): benchmarks/main.cpp benchmarks/tgen_cases.cpp benchmarks/jngen_cases.cpp benchmarks/benchmark.h benchmarks/cases.h vendor/tgen/single_include/tgen.h vendor/jngen/jngen.h
	@mkdir -p build/benchmarks results
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ \
		benchmarks/main.cpp benchmarks/tgen_cases.cpp benchmarks/jngen_cases.cpp

benchmark: vendor $(BENCH_BIN)
	@mkdir -p docs
	./$(BENCH_BIN) --json $(BENCH_JSON)

$(VIZ_BIN): visualize/main.cpp visualize/tgen_samples.cpp visualize/jngen_samples.cpp visualize/samples.h vendor/tgen/single_include/tgen.h vendor/jngen/jngen.h
	@mkdir -p build/visualize results/svg docs/gallery
	$(CXX) $(CXXFLAGS) $(INCLUDES) -o $@ \
		visualize/main.cpp visualize/tgen_samples.cpp visualize/jngen_samples.cpp

visualize: vendor $(VIZ_BIN)
	@mkdir -p results/svg docs/gallery
	rm -f docs/gallery/*.svg results/svg/*
	./$(VIZ_BIN)
	python3 visualize/render_tgen.py results/svg docs/gallery
	cp results/svg/*_jngen_s*.svg docs/gallery/ 2>/dev/null || true
	python3 visualize/normalize_gallery.py docs/gallery

$(TGEN_XML_INDEX): vendor
	@mkdir -p $(TGEN_DOC_BUILD)
	@printf '%s\n' '<div id="benchmark-results"></div>' > $(TGEN_DOC_BUILD)/benchmark_include.html
	cd vendor/tgen/docs && { \
	printf '%s\n' '@INCLUDE = Doxyfile' 'GENERATE_HTML = NO' 'GENERATE_XML = YES' \
		'GENERATE_LATEX = NO' 'GENERATE_DOCBOOK = NO' \
		'OUTPUT_DIRECTORY = build' 'XML_OUTPUT = xml' \
		'NUM_PROC_THREADS = $(TGEN_DOC_NPROCS)' 'DOT_NUM_THREADS = $(TGEN_DOC_NPROCS)'; \
	} | doxygen -

docs: $(TGEN_XML_INDEX)
	python3 docs/render_docs.py
	cd vendor/tgen && python3 docs/llms_gen.py \
		--xml docs/build/xml \
		--out docs/build \
		--base-url 'https://brunomaletta.github.io/tgen'
	cd vendor/tgen && python3 docs/benchmark_render.py \
		--json docs/benchmark_results.json \
		--xml docs/build/xml \
		--out docs/build/benchmark_include.html
	cd vendor/tgen/docs && { \
	printf '%s\n' '@INCLUDE = Doxyfile' \
		'NUM_PROC_THREADS = $(TGEN_DOC_NPROCS)' 'DOT_NUM_THREADS = $(TGEN_DOC_NPROCS)'; \
	} | doxygen -
	python3 docs/build_site.py --bundle-only

check:
	python3 docs/check_docs.py

site: vendor docs
	python3 docs/build_site.py --site-dir docs/site

doc: docs

opendoc:
	@test -f '$(DOC_PATH)' || { printf '%s\n' "opendoc: missing $(DOC_PATH) - run 'make docs' first." >&2; exit 1; }
	@{ \
	if command -v google-chrome >/dev/null 2>&1; then \
		( google-chrome 'file://$(DOC_PATH)' </dev/null >/dev/null 2>&1 & ); \
	elif command -v google-chrome-stable >/dev/null 2>&1; then \
		( google-chrome-stable 'file://$(DOC_PATH)' </dev/null >/dev/null 2>&1 & ); \
	elif command -v xdg-open >/dev/null 2>&1; then \
		( xdg-open '$(DOC_PATH)' </dev/null >/dev/null 2>&1 & ); \
	elif command -v chromium >/dev/null 2>&1; then \
		( chromium 'file://$(DOC_PATH)' </dev/null >/dev/null 2>&1 & ); \
	elif command -v chromium-browser >/dev/null 2>&1; then \
		( chromium-browser 'file://$(DOC_PATH)' </dev/null >/dev/null 2>&1 & ); \
	else \
		printf '%s\n' "opendoc: no Chrome or xdg-open on PATH. Open in a browser:" >&2; \
		printf '%s\n' "  file://$(DOC_PATH)" >&2; \
		exit 1; \
	fi; \
	}

clean:
	rm -rf build results
