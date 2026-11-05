//
// pomocni operator za ispis trenutno najboljeg rjesenja
//

bool evaluateVerbose;

#include"GPSymbRegEvalOp.h"


class WriteBest : public Operator
{
private:
	StateP state_;
	uint freq, maxGen, eval;
	double fitnessVal;
	bool termEval, termFitness, termStagn, termGen;
	uint logFrequency;

public:

	void registerParameters(StateP state)
	{
		state->getRegistry()->registerEntry("bestfile", voidP(), ECF::STRING, "file to store best ind after each generation");
	}

	bool initialize(StateP state)
	{
		termEval = termFitness = termStagn = termGen = false;

		if(state->getRegistry()->isModified("term.eval"))
			termEval = true;
		if(state->getRegistry()->isModified("term.stagnation"))
			termStagn = true;
		if(state->getRegistry()->isModified("term.fitnessval"))
			termFitness = true;
		if(state->getRegistry()->isModified("term.maxgen"))
			termGen = true;

		state_ = state;
		voidP sptr = state->getRegistry()->getEntry("term.stagnation");
		freq = *((uint*)sptr.get());

		sptr = state->getRegistry()->getEntry("term.maxgen");
		maxGen = *((uint*)sptr.get());

		sptr = state->getRegistry()->getEntry("term.eval");
		eval = *((uint*)sptr.get());

		sptr = state->getRegistry()->getEntry("term.fitnessval");
		fitnessVal = *((double*)sptr.get());

		sptr = state->getRegistry()->getEntry("log.frequency");
		logFrequency = *((uint*)sptr.get());

		return true;
	}

	bool operate(StateP state)
	{
		bool output = false;
		bool writtenBest = false;
		uint currentGen = state->getGenerationNo();
		double minFitness = state->getStats()->getFitnessMin();
		double maxFitness = state->getStats()->getFitnessMax();

		ECF_LOG(state, 3, "Best in " + uint2str(state->getGenerationNo()));
		IndividualP bestInd = state->getPopulation()->getHof()->getBest().at(0);

		if (state->getGenerationNo() % logFrequency == 0) {
			writtenBest = true;
			//GPSymbRegEvalOp* op = (GPSymbRegEvalOp*)state->getEvalOp().get();
			evaluateVerbose = true;
			state->getAlgorithm()->evaluate(bestInd);
			evaluateVerbose = false;
		}

		ECF_LOG(state, 3, bestInd->toString());

		if(termGen && currentGen >= maxGen)
			output = true;

		if(termStagn && (currentGen - state->getPopulation()->getHof()->getLastChange()) > freq)
			output = true;

		if(termEval && state->getEvaluations() >= eval)
			output = true;

		if(termFitness && (fitnessVal >= minFitness && fitnessVal <= maxFitness))
			output = true;

		if (output && !writtenBest) {
			std::vector<IndividualP> hof = state->getHoF()->getBest();
			IndividualP ind = hof[0];

			evaluateVerbose = true;
			state->getAlgorithm()->evaluate(ind);
			evaluateVerbose = false;

			//ECF_LOG(state, 1, ind->toString());
		}

		return true;
	}
};