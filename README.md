To test the NPE benchmark:

1. Download materials
```bash
git clone https://github.com/symlog/symlog.git
wget https://drive.google.com/file/d/1Bc_xjBuCE0eiFz9lupcZP6NMR0k_n-zw/view?usp=share_link
tar -zxvf exp-data.tar.gz -C /path/to/data_directory
```

2. Prepare the environment
```
conda create -n npe python=3.10
conda activate npe
pip install -r requirements.txt
```

3. Run the benchmark
```
cd symlog
python run.py --data_path /path/to/data_directory --analyzer_path may-cfg.dl
```

Note: `TODO` and `FIXME` comments in code indicate the function has not been implemented yet and dirty hacks are used to make the code run.