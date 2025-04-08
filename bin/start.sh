main() {
  project_dir=$(cd $(dirname $(dirname $0)); pwd)

  cd $project_dir && python $project_dir/app/server/bootstrap.py
}

main

