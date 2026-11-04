#include "GPSymbRegEvalOp.h"

#include "IASin.h"
#include "IATree.h"
#include <cmath>

void IASin::execute(void* result, Tree::Tree& tree)
{
	if (!calculateBoundsIfRootNode(result, tree)) {
		return;
	}

	Tree::Primitives::Sin::execute(result, tree);
}

IABounds IASin::calculateBounds(Tree::IATree& tree) {
	// get next argument
	tree.iNode_++;
	IAPrimitiveP prim = std::dynamic_pointer_cast<IAPrimitive>(tree[tree.iNode_]->primitive_);
	// calculate bounds
	IABounds bounds = prim->calculateBounds(tree);

	if (!bounds.isWithinBounds) {
		// subtree not within bounds, delete expression
		return bounds;
	} else {
		// subtree is ok
		IABounds retVal;
		retVal.isWithinBounds = true;
		retVal.isLowerBoundInclusive = true;
		retVal.lowerBound = -1.0;
		retVal.isUpperBoundInclusive = true;
		retVal.upperBound = 1.0;
		return retVal;
	}
}
