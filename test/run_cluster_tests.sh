source ~/.bashrc
conda activate py
cd ~/TCutility
git switch main
git pull
cd test
pytest cluster_tests >> TCutility_cluster_test_$(date + %F_%T).out