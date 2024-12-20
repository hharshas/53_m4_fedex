cmake_minimum_required(VERSION 3.20.0)
project(fedex)

add_executable(main first_fit.cpp)
target_compile_features(main PRIVATE cxx_std_20)