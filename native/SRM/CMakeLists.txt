# gep/ is not listed: it is an old copy of ecf/gep kept from the original source.
add_executable(SRM
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

target_link_libraries(SRM PRIVATE ECF)

# The app expects the binary at srm/SRM (srm/SRM.exe on Windows). The generator
# expression stops multi-config generators from adding a Release/ subfolder.
set_target_properties(SRM PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY "$<1:${SRM_OUTPUT_DIR}>"
)
