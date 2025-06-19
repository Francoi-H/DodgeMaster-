import pandas as pd
import matplotlib.pyplot as plt

def analyze_game_log(filepath="data/game_log.csv"):
    df = pd.read_csv(filepath)
    print(df.head())

    plt.figure(figsize=(10, 5))
    score_over_time = df[df['event'] == 'missed']
    plt.plot(score_over_time['score'], label='Score over time', color='blue')
    plt.title("Score Progression")
    plt.xlabel("Time Step")
    plt.ylabel("Score")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig("data/score_plot.png")
    plt.show()

    event_counts = df['event'].value_counts()
    plt.figure()
    event_counts.plot(kind='bar', color=['green', 'red'])
    plt.title("Event Frequency")
    plt.ylabel("Count")
    plt.tight_layout()
    plt.savefig("data/events_plot.png")
    plt.show()
