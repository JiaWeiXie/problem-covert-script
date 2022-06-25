# DomJudge Problem convert script

Multi testcase convert to single testcase

## Usage

```shell
# Basic usage
$ python main.py <problem-zip> 

# Basic usage
$ python main.py <problem-folder> 

# Show detail, log level info
$ python main.py example/1101B4 -v

# Show detail, log level debug
$ python main.py example/1101B4 -vv


# Ignore input test data first line
$ python main.py example/1101B2 -l

# Ignore input test data two lines
$ python main.py <problem> -ll

# Specify output path
$ python main.py example/1101B4 -o <path>

# Show help
$ python main.py -h
usage: main.py [-h] [-o OUTPUT] [-l] [-v] problem

positional arguments:
  problem               A problem folder or zip file path.

optional arguments:
  -h, --help            show this help message and exit
  -o OUTPUT, --output OUTPUT
                        Output base folder path.
  -l, --lines           ignore input testcase lines, -l: one line, -ll: two lines.
  -v, --verbose         -v: INFO, -vv: DEBUG, default: WARNING.
```

## Testcase format

### example 1

1.in
```
1 1
2 2
```

1.ans
```
2
4
```

convert

101.in
```
1 1
```

102.in
```
2 2
```

101.ans
```
4
```

102.ans
```
2
```

### example 2

`$ python main.py <problem> -l`

1.in
```
2
1 1
2 2
```

1.ans
```
2
4
```

convert

101.in
```
1 1
```

102.in
```
2 2
```

101.ans
```
4
```

102.ans
```
2
```