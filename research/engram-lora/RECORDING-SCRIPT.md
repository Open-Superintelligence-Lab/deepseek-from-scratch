# Research segment: can a frozen model swap learned memories?

## 1. Question — show the frozen model and two removable modules

So far, we've explained how Engram works. Now I want to show you how we can turn
that understanding into a research experiment. Here's our question: can we take
an already-trained language model, keep its original weights frozen, and give it
different specialties by plugging in different learned memory modules?

For example, we could load one module for financial text and another for code.
We aren't claiming to have invented n-gram memory. We're testing whether an
Engram-inspired module is useful in this particular setup.

## 2. Setup — show the data and what is trainable

We used SmolLM2, a small model with about 135 million parameters. We downloaded
real financial discussions from FiQA and real Ruby functions from CodeSearchNet.
We kept the model itself frozen and trained separate memory modules on the two
datasets. Each module includes the tables and a small network that reads them.

We trained on about 65,000 tokens per domain, tried two module sizes, and repeated
the comparison with three random seeds. We chose training settings using a
validation set, then measured predictions on separate test text. For code, the
training and test examples come from different repositories.

This is a small adaptation experiment, not a reproduction of DeepSeek's full
pretraining run. We also don't know which examples the original model might have
encountered during its own pretraining.

## 3. Results — show the three-row switching table

The matching modules improved prediction. On code, the original model scored
23.44 perplexity, and loading the code module improved that to 19.64. Lower is
better: it means the model assigns more probability to the actual next tokens.
The finance module also helped on financial text, though the improvement was smaller.

We could switch from finance to code and back, and restore exactly the same
predictions. So we have working removable specialists. That does not mean we
have verified a reliable coding assistant or a financial adviser; we're measuring
next-token prediction on held-out text.

## 4. Honest comparison — show LoRA results briefly

We also compared against LoRA, using similar trainable parameter counts and the
same data and tuning budget. LoRA learned both domains better. Enlarging our
memory tables didn't improve this pilot either. So our initial idea that n-gram
memory might be the better adapter was not supported by these results.

The memory modules changed general-text performance less, but they also learned
less. We can't claim better preservation without comparing methods at the same
amount of task improvement.

## 5. Follow-up — show tables versus reader

Then we asked: could we swap only the memory tables? In a one-seed diagnostic,
the code tables with the finance reader scored 23.29 on code, compared with
19.64 for the complete code module. So the learned specialty isn't entirely
inside the tables. The reader matters too.

That gives us a specific next research question: can we train one shared reader
to work with several interchangeable memory tables? We haven't tested that yet.
The point of research is to make a clear prediction, test it, and let the result
decide our next question—even when the first idea doesn't win.

## Optional cost explanation

Making the tables larger adds stored vectors. If we keep the number and width of
lookups fixed, we still retrieve only four vectors per token in this implementation.
The model doesn't scan every row. But storage grows, loading a module requires
more transfer, and our current dense optimizer also uses more training memory
and table-update work. Cheap additional storage capacity doesn't mean free training.

## Files and publication

Keep this study in the existing deepseek-from-scratch repository, under
research/engram-lora. Publish code, protocol, small result files and the write-up.
Keep the full GPU backup, model adapters and dataset copies outside Git commits.
A standalone repository can wait until this becomes an independently useful library.
