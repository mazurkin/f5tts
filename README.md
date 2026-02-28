# f5tts environment

## install

```shell
# first, make an isolated Conda environment with Python, Poetry and CUDA inside
$ make env-init-conda

# then install the most of the dependencies with Poetry
$ make env-init-poetry
```

## run

```shell
bin/voice_clone.sh \
  --ref_audio "work/origin.wav" \
  --text 'Hello World! This is a test of the voice cloning system.' \
  --output output.wav \
  --speed 0.8 \
  --nfe_step 64 \
  --cfg_strength 2.9
```
