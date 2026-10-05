
cmake_minimum_required(VERSION 3.19)

project(mooncake_app_pro VERSION 0.1.0 LANGUAGES C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# 供 IDE（.vscode/c_cpp_properties.json）做精确索引
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# 可执行产物统一输出到构建目录根部（否则会落在 platforms/desktop/ 子目录里）
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

add_subdirectory(platforms/desktop)

