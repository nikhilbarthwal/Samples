cmake_minimum_required(VERSION 3.16)
project(SineWaveQt LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Let CMake run Qt's meta-object / resource / UI compilers automatically.
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_AUTOUIC ON)

if(NOT CMAKE_BUILD_TYPE)
    set(CMAKE_BUILD_TYPE Release)
endif()

# Qt6 comes from apt (system path) and Matplot++ from /usr/local; both are on
# CMake's default search path. If you installed Matplot++ to ~/.local instead,
# uncomment:
#
# list(APPEND CMAKE_PREFIX_PATH "$ENV{HOME}/.local")

find_package(Qt6 REQUIRED COMPONENTS Widgets)
find_package(Matplot++ REQUIRED)

add_executable(sine_wave_qt main.cpp)

target_link_libraries(sine_wave_qt
    PRIVATE
        Qt6::Widgets          # pulls in Qt Gui + Core transitively
        Matplot++::matplot
)
