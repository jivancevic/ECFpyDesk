#include "GPSymbRegEvalOp.h"

#include "IATree.h"
#include "IAERCD.h"
#include <cmath>

void IAERCD::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}

	Tree::Primitives::ERCD::execute(result, tree);
}

IABounds IAERCD::calculateBounds(Tree::IATree& tree) {
	IABounds retVal;
	double val = this->value_;

	retVal.isWithinBounds = true;
	retVal.isLowerBoundInclusive = true;
	retVal.lowerBound = val;
	retVal.isUpperBoundInclusive = true;
	retVal.upperBound = val;
	return retVal;
}
