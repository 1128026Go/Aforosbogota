"""Test segmentation algorithm directly"""
import json
import pickle
from pathlib import Path
from services.trajectory_processor import TrajectoryProcessor

data_dir = Path('data') / 'dataset_f8144347'
cardinals_file = data_dir / 'cardinals.json'
pkl_file = data_dir / 'raw.pkl'

# Load
cardinals = json.load(open(cardinals_file, encoding='utf-8'))
accesses = cardinals['accesses']

# Load a track from raw.pkl to test
raw_data = pickle.load(open(pkl_file, 'rb'))

# Create processor
processor = TrajectoryProcessor('dataset_f8144347')

# Find track_7063 from playback
playback_file = data_dir / 'playback_events.json'
playback = json.load(open(playback_file, encoding='utf-8'))

track_7063 = None
for event in playback['events']:
    if event['track_id'] == 'track_7063':
        track_7063 = event
        break

if not track_7063:
    print("Track not found!")
else:
    print(f"Testing track_7063:")
    print(f"  Positions: {len(track_7063['positions'])}")
    print(f"  Class: {track_7063['class']}")

    # Create a track dict in the format expected by _segment_trajectory
    track_dict = {
        'track_id': 'track_7063',
        'positions': track_7063['positions'],
        'frames': list(range(track_7063['frame_entry'], track_7063['frame_exit'] + 1)),  # Reconstruct frames
        'class': track_7063['class']
    }

    # Call segmentation
    print(f"\nCalling _segment_trajectory...")
    segments = processor._segment_trajectory(track_dict, accesses)

    print(f"\nResult: {len(segments)} segments")
    for seg in segments:
        print(f"  Segment {seg['segment_index']}: {seg['entry_cardinal']} -> {seg['exit_cardinal']}")
        print(f"    Entry frame: {seg['entry_frame']}, Exit frame: {seg['exit_frame']}")
        print(f"    Positions: {len(seg['positions'])}")
