

# tools
E := @echo
ANTLR4 := $(shell if [ -n "$$VIRTUAL_ENV" ] && [ -x "$$VIRTUAL_ENV/bin/antlr4" ]; then echo "$$VIRTUAL_ENV/bin/antlr4"; elif [ -x /usr/bin/antlr4 ]; then echo /usr/bin/antlr4; else echo antlr4; fi)


all: parser


GRAMAR_FILES = CBBsdl.g4 \
			   CBBsdlLexer.g4

ANTLR4_FILES = CBBsdlParser.py CBBsdlLexer.py CBBsdlListener.py \
			   CBBsdl.tokens  CBBsdl.interp \
			   CBBsdlLexer.tokens CBBsdlLexer.interp
# 			   .antlr


parser: $(ANTLR4_FILES)


$(ANTLR4_FILES): $(GRAMAR_FILES)
	$(E) "Generating python code from ANTLR grammar files..."
	@$(ANTLR4) -Dlanguage=Python3 $(GRAMAR_FILES)


clean:
	$(E) "Cleaning up generated files..."
	@rm -rf $(ANTLR4_FILES)
	@rm -rf __pycache__
	@rm -rf */__pycache__