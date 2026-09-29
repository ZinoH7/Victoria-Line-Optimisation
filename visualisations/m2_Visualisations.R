library(readr)
library(ggplot2)
library(tidyverse)


vic_mon <- read_csv("~/Tube service optimisation/data/processed/Optimised_m2_results.csv")


# Combine directions into one column

vic_mon_merged <- pivot_longer(vic_mon, 
                               cols = c('NB', 'SB'),
                               names_to = 'Direction',
                               values_to = 'Trains_Dispatched')

# Fix times

vic_mon_merged$Start_Time <- vic_mon_merged$Time 

vic_mon_merged <- vic_mon_merged %>% 
  separate(Start_Time, into = c("Start_Time", "End Time"), sep = "-")

vic_mon_merged$Start_Time <- hms::as_hms(
  paste0(substr(vic_mon_merged$Start_Time, 1, 2),":",
    substr(vic_mon_merged$Start_Time, 3, 4),":00"
  )
)

# Time Series Plots

# Dispatched trains

ggplot(vic_mon_merged, aes(x = Start_Time, y = Trains_Dispatched, 
                           group = Direction, colour = Direction)) + 
  geom_step(linewidth = 1) + 
  geom_point() + 
  theme_minimal() + 
  labs(
    title = "Optimised Train Dispatches",
    x = "15 minute interval",
    y = "Number of Trains Dispatched") +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = "top")
  

# Trains Active
ggplot(vic_mon_merged, aes(x=Start_Time, y= Trains_active)) + 
  geom_step(linewidth = 1) + 
  geom_point(size = 1.5) + 
  labs(
    title = "Optimised Active Trains",
    x = "15 minute interval",
    y = "Number of Trains active"
  ) + theme_minimal() +
  theme(
    plot.title = element_text(face = "bold")
    )



#df for direction
dispatch <- vic_mon_merged[c("Start_Time", "Direction", 
                                  "Trains_Dispatched", "t")]

# df for active
active <- vic_mon_merged[c("Start_Time", "Trains_active", 
                                    "Trains_Dispatched", "t")]


#Plot

ggplot(dispatch, aes(x = t, y = Trains_Dispatched, 
                           group = Direction, 
                     colour = Direction)) + 
  geom_step(linewidth = 1) + 
  geom_point(size = 2) + 
  geom_step(data = active, aes(x = t,
                               y = Trains_active,
                               colour = "Active Trains"),
            inherit.aes = FALSE,
            linewidth = 1
    ) + geom_point(data = active, size = 2, inherit.aes = FALSE,
                   aes(x = t,
                               y = Trains_active,
                               colour = "Active Trains")) + 
  scale_x_continuous(breaks = active$t[seq(1, nrow(active), by = 20)],
    labels = active$Start_Time[seq(1, nrow(active), by = 20)]
  ) +
  theme_minimal() + 
  labs(
    title = "Optimised Train Dispatches",
    x = "15 minute interval",
    y = "Number of Trains") +
  theme(
    plot.title = element_text(face = "bold"),
    legend.position = "top")


