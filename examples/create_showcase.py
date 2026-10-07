"""Create a self-contained arithmetic forecasting example, not research evidence."""
import argparse
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import paper
from create_demo import create


def create_showcase(destination):
    root = create(destination, 'generated')
    training = [2, 4, 6, 8]
    heldout = [10, 12]
    step = (training[-1] - training[0]) / (len(training) - 1)
    forecast = [training[-1] + step * i for i in (1, 2)]
    baseline = [training[-1]] * 2
    result = {'training': training, 'heldout': heldout, 'forecast': forecast,
              'baseline': baseline, 'model_mae': sum(abs(a-b) for a,b in zip(heldout, forecast))/2,
              'baseline_mae': sum(abs(a-b) for a,b in zip(heldout, baseline))/2}
    paper.write(root/'result.json', result)
    paper.write(root/'model-review.json', {'reviewer':'synthetic fixture author', 'notes':'Constructed linear sequence and holdout arithmetic only; no generalization claim.', 'relations':[{'id':'R1','given':'four linear training values, two future heldout values','interpretation':'arithmetic trend and last-value baseline','choice':'as_given','reason':'self-contained software fixture','status':'accepted'}]})
    plan = paper.read(root/'paper-plan.json')
    plan['title'] = 'Synthetic Forecasting Walkthrough'
    plan['evidence']['E1']['sha256'] = paper.digest(root/'result.json')
    plan['claims'] = {name: {'evidence': 'E1', 'pointer': '/'+field, 'value': result[field], 'format': '.1f'}
                      for name,field in [('MODEL','model_mae'),('BASE','baseline_mae')]}
    paper.write(root/'paper-plan.json', plan)
    (root/'section.md').write_text('''## Question and evidence

How does a simple trend compare with a last-value baseline? This is a deliberately constructed software fixture, not a competition paper or a model effectiveness study. All values are synthetic and saved in result.json.

## Model and split

Only observations 1-4 fit the trend. Observations 5-6 are held out. The average step is computed from the first and last training values. The baseline repeats the final training value.

$$
\\hat{y}_{t+h}=y_t+h\\frac{y_t-y_1}{t-1}
$$

| Observation | Split | Actual | Trend forecast | Last-value baseline |
| --- | --- | --- | --- | --- |
| 1-4 | Training | 2, 4, 6, 8 | Not evaluated | Not evaluated |
| 5 | Holdout | 10 | 10 | 8 |
| 6 | Holdout | 12 | 12 | 8 |

## Computed result

Trend MAE: [[value:MODEL]]. Baseline MAE: [[value:BASE]]. Each value is bound to a JSON pointer and source hash. The trend matches because the fixture was constructed to be linear; this is not evidence of generalization.

## What the workflow checks

The authoring audit checks the evidence hash, claim values, section coverage and model-review record. Build produces LaTeX; render compiles a PDF. A separate visual review is still required before verify can pass.

## What remains outside the example

Real data provenance, alternative models, uncertainty and independent mathematical review are not demonstrated. Do not reuse these numbers in a research conclusion. Changing result.json requires regenerating its evidence hash and rebuilding downstream outputs.
''', encoding='utf-8')
    return root

if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--destination', type=Path, required=True)
    args=parser.parse_args()
    print(create_showcase(args.destination))
