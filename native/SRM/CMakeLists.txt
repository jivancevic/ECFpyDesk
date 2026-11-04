cmake_minimum_required(VERSION 2.8)
project(SRM)

# try setting dir manually if environment variable is not set
#set (BOOST_ROOT "C:/Program Files/boost_1_74_0")

set(SOURCE_FILES
        Avg.h
        DataWriter.h
        ErrorMetric.h
        Evaluator.h
        FileDataWriter.h
        IAAdd.h
        IAConstTerminal.h
        IACos.h
        IADiv.h
        IAERCD.h
        IALog.h
        IAMul.h
        IAPrimitive.h
        IASin.h
        IASqrt.h
        IASub.h
        IATerminal.h
        IATree.h
        infixTree.h
        Log.h
        MeanAbsoluteErrorMetric.h
        MeanAbsolutePercentageErrorMetric.h
        MeanSquareErrorMetric.h
        ReadData.h
        GEPSymbRegEvalOp.h
        GPSymbRegEvalOp.h
        Sqrt.h
        WriteBest.h
        DataWriter.cpp
        Evaluator.cpp
        FileDataWriter.cpp
        IAAdd.cpp
        IAConstTerminal.cpp
        IACos.cpp
        IADiv.cpp
        IAERCD.cpp
        IALog.cpp
        IAMul.cpp
        IASin.cpp
        IASqrt.cpp
        IASub.cpp
        IATerminal.cpp
        IATree.cpp
        Log.cpp
        main.cpp
        GEPSymbRegEvalOp.cpp
        GPSymbRegEvalOp.cpp
        MeanAbsoluteErrorMetric.cpp
        MeanAbsolutePercentageErrorMetric.cpp
        MeanSquareErrorMetric.cpp
        Sqrt.cpp
)

include_directories(../../)
add_executable(SRM ${SOURCE_FILES})

if(CMAKE_BUILD_TYPE STREQUAL "Debug")
    target_link_libraries(SRM ${CMAKE_CURRENT_SOURCE_DIR}/../../debug/libECF.a)
    set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -g")
endif()
if(CMAKE_BUILD_TYPE STREQUAL "Release")
    target_link_libraries(SRM ${CMAKE_CURRENT_SOURCE_DIR}/../../release/libECF.a)
endif()