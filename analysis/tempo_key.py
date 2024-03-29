
import essentia.standard as es

# Compute all features, aggregate only 'mean' and 'stdev' statistics for all low-level, rhythm and tonal frame features
features, features_frames = es.MusicExtractor(lowlevelStats=['mean', 'stdev'],
                                              rhythmStats=['mean', 'stdev'],
                                              tonalStats=['mean', 'stdev'])('/home/dev/crec/GoldLink/At What Cost/Crew (feat. Brent Faiyaz & Shy Glizzy).flac')

# See all feature names in the pool in a sorted order
print(sorted(features.descriptorNames()))
