python_path = ..
verilog_files = pdm2pcm.v

all: $(verilog_files)

pdm2pcm.v: $(python_path)/pdm2pcm.py

%.v:
	python $< generate -t v > $@

clean:
	rm -rf *.v
