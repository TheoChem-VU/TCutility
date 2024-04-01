source ~/.bashrc
conda activate py
cd ~/TCutility
#git switch main
git pull
cd test/cluster_tests
outf="results/TCutility_cluster_test_$(date +%F_%T).out"
echo "Git branch $(git branch)" >> outf
echo "$Git version $(git describe --tags)" >> outf

sbatch --job-name="TCutility $(git describe --tags)" -p tc --wrap="pytest >> $outf"
