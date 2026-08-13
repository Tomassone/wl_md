# RGBDS toolchain
RGBASM  := rgbds/rgbasm
RGBLINK := rgbds/rgblink
RGBFIX  := rgbds/rgbfix

# Build parameters — pass via command line:
#   make SOURCE=config-original FILENAME=wl COMPARISON=original.md25s [NOFIX=1]
SOURCE     ?=
FILENAME   ?=
COMPARISON ?=
NOFIX      ?=

.PHONY: all clean
.DELETE_ON_ERROR:

# -----------------------------------------------------------------------------
# Guard: if FILENAME is empty, refuse to run (like the batch file)
# -----------------------------------------------------------------------------
ifeq ($(FILENAME),)

all:
	@echo "Don't execute this file directly."
	@exit 1

clean:
	@echo "Nothing to clean (FILENAME not set)."

# -----------------------------------------------------------------------------
# Normal build path
# -----------------------------------------------------------------------------
else

all: build

# Final target: fix, compare, done
build: $(FILENAME).md25s
ifeq ($(NOFIX),)
	@echo "Fixing header checksum..."
	$(RGBFIX) -v $(FILENAME).md25s -p 0
endif
	@if [ -n "$(COMPARISON)" ] && [ -f "$(COMPARISON)" ]; then \
		cmp -l "$(FILENAME).md25s" "$(COMPARISON)" || true; \
	fi

# Assembly step
$(FILENAME).o: $(SOURCE).asm
	@echo "Assembling..."
	@$(RGBASM) -v -o $(FILENAME).o $(SOURCE).asm || \
		{ echo "Error while assembling."; \
		  echo "=========================="; \
		  echo "  Build failure."; \
		  echo "=========================="; \
		  exit 1; }

# Link step
$(FILENAME).md25s: $(FILENAME).o
	@echo "Linking..."
	@$(RGBLINK) -v -m $(FILENAME).map -n $(FILENAME).sym -p 0 -d -o $(FILENAME).md25s $(FILENAME).o || \
		{ echo "Error while linking."; \
		  echo "=========================="; \
		  echo "  Build failure."; \
		  echo "=========================="; \
		  exit 1; }
	@echo "=========================="
	@echo "  Build Success."
	@echo "=========================="

clean:
	rm -f $(FILENAME).o $(FILENAME).map $(FILENAME).sym $(FILENAME).md25s

endif