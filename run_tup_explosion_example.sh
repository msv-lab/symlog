python3.10 src/transform_to_meta_program.py

cd tests

echo "Running original example"
if [ ! -d "original_results" ]; then
    mkdir original_results
fi
souffle -o original original_program.dl --jobs=auto
./original -Doriginal_results/ --jobs=auto
echo "Done. Results are in tests/original_results/"

echo "Running small transformed example"
if [ ! -d "small_transformed_results" ]; then
    mkdir small_transformed_results
fi
souffle -o small_transformed small_transformed_program.dl --jobs=auto
./small_transformed -Dsmall_transformed_results/ --jobs=auto
echo "Done. Results are in tests/small_transformed_results/"

echo "DID NOT run the large transformed example, since runing it will exceeds the memory limit. If you want to run it, please comment out the last 5 lines of run_tup_explosion_example.sh"
# if [ ! -d "large_transformed_results" ]; then
#     mkdir large_transformed_results
# fi
# souffle -o large_transformed large_transformed_program.dl --jobs=auto
# ./large_transformed -Dlarge_transformed_results/ --jobs=auto
