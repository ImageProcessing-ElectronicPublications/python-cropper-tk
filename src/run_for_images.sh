#! /bin/bash
for img in $1/*
do 
    echo $img
    if [[ "$img"=*.jpg ]]
    then
        echo $img
        python croppertk.py $img
    fi
done