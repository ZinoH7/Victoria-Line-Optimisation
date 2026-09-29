library(readr)
library(ggplot2)
library(tidyverse)
library(patchwork)

## Bar plot of total trains dispatched vs train capacity

min_total <-  read_csv("~/Tube service optimisation/data/processed/Trains_Sensitivity.csv")

min_total$Capacity <- as.character(min_total$Capacity)

ggplot(min_total, aes(x = Capacity, y = Minimised_trains,
                      fill = Capacity,
                      colour = Capacity)) +
  geom_bar(stat = "identity") +
  labs(title = "Total Trains dispatched vs Train Capacity",
       x = "Train Capacity", y = "Total Trains Dispatched") +
  theme_minimal()



vic_mon <- read_csv("~/Tube service optimisation/data/processed/Sensitivity_m2.csv")

# Direction to one column

vic_mon <- pivot_longer(vic_mon, 
                               cols = c('NB', 'SB'),
                               names_to = 'Direction',
                               values_to = 'Trains_Dispatched')

# Fix times

vic_mon$Start_Time <- vic_mon$Time 

vic_mon <- vic_mon %>% 
  separate(Start_Time, into = c("Start_Time", "End Time"), sep = "-")

vic_mon$Start_Time <- paste0(
  substr(vic_mon$Start_Time, 1, 2),
  ":",
  substr(vic_mon$Start_Time, 3, 4)
)

vic_mon$Capacity <- as.character(vic_mon$Capacity)

# Plot trains active for each interval, split by capacity

ggplot(vic_mon, aes(x = t, 
                    y = Trains_active,
                    group = Capacity, 
                    colour = Capacity)) + 
  geom_step(linewidth = 1) + 
  geom_point(size = 1.5) + 
  labs(
    title = "Minimised Active Trains",
    x = "Time",
    y = "Number of Trains Active"
  ) +
  scale_x_continuous(breaks = vic_mon$t[seq(1, nrow(vic_mon), by = 80)],
                     labels = vic_mon$Start_Time[seq(1, nrow(vic_mon), by = 80)]) +
  theme_minimal() +
  theme(
    plot.title = element_text(face = "bold")
  )

# Dispatch schedule for selected capacities

#df for direction
dispatch <- vic_mon[c("Start_Time", "Direction", 
                             "Trains_Dispatched", "t", "Capacity")]

# df for active
active <- vic_mon[c("Start_Time", "Trains_active", 
                           "Trains_Dispatched", "t", "Capacity")]

# create function for plot

plot_capacity <- function(capacity) {
  
  plot_data1 <- dispatch %>%
    filter(Capacity == capacity)
  
  plot_data2 <- active %>%
    filter(Capacity == capacity)
  
  ggplot(plot_data1, aes(x = t, y = Trains_Dispatched, 
                       group = Direction, 
                       colour = Direction)) + 
    geom_step(linewidth = 1) + 
    geom_point(size = 1) + 
    geom_step(data = plot_data2, aes(x = t,
                                 y = Trains_active,
                                 colour = "Active Trains"),
              inherit.aes = FALSE,
              linewidth = 1
    ) + geom_point(data = plot_data2, size = 1, inherit.aes = FALSE,
                   aes(x = t,
                       y = Trains_active,
                       colour = "Active Trains")) + 
    scale_x_continuous(breaks = plot_data2$t[seq(1, nrow(plot_data2), by = 20)],
                       labels = plot_data2$Start_Time[seq(1, nrow(plot_data2), by = 20)]
    ) +
    theme_minimal() + 
    labs(
      title = paste("Optimised Train Dispatches at capacity", capacity),
      x = "15 minute interval",
      y = "Number of Trains") +
    theme(
      plot.title = element_text(face = "bold"),
      legend.position = "top")
}

p1 <- plot_capacity(856)
p2 <- plot_capacity(749)
p3 <- plot_capacity(642)
p4 <- plot_capacity(428)

combined_plot <- (p1 + p2) / (p3 + p4)

combined_plot