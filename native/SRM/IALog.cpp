#include "GPSymbRegEvalOp.h"

#include "IALog.h"
#include "IATree.h"
#include <cmath>

void IALog::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}
	
	Tree::Primitives::Log::execute(result, tree);
}

IABounds IALog::calculateBounds(Tree::IATree& tree) {
	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds = prim->calculateBounds(tree);

	if (!bounds.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds;
	} else if (bounds.lowerBound < 0 || (bounds.lowerBound == 0 && bounds.isLowerBoundInclusive)) {
		IABounds retVal;
		retVal.isWithinBounds = false;
		return retVal;
	} else {
		// subtree is ok
		IABounds retVal;
		retVal.isWithinBounds = true;
		retVal.isLowerBoundInclusive = bounds.isLowerBoundInclusive;
		retVal.lowerBound = log10(bounds.lowerBound);
		retVal.isUpperBoundInclusive = bounds.isUpperBoundInclusive;
		retVal.upperBound = log10(bounds.upperBound);
		return retVal;
	}
}
