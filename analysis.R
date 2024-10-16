library(magrittr)
library(dplyr)
library(stringr)
library(stopwords)
library(tm)
library(textstem)
library(microbenchmark)
library(str2str)

# options(max.print=3500)

male <- VCorpus(DirSource("dataset/male"), readerControl=list(language='ko'))
female <- VCorpus(DirSource("dataset/female"), readerControl=list(language='ko'))

specialChars = '(ㆍ|「|】|、|ㅣ|…|」|”|』|“|『|＊|Ｌ|：|‥|《|※|》)'
removeSpecialChars <- function(x) gsub(specialChars, '', x)

preprocessing <- function(vcorpus) vcorpus %>%
  tm_map(removeNumbers) %>%
  tm_map(removePunctuation) %>%
  tm_map(content_transformer(str_squish)) %>%
  tm_map(content_transformer(removeSpecialChars)) %>%
  tm_map(stripWhitespace) %>%
  tm_map(content_transformer(scan_tokenizer)) # %>%
  # tm_map(content_transformer(lemmatize_strings)) # %>%
  # tm_map(removeWords, stopwords("english")) # %>%
  # tm_map(stemDocument) # %>% 

# stopwords::stopwords('ko', source='stopwords-iso')
# stopwords::stopwords('ko', source='marimo')
# microbenchmark(preprocessing(male), preprocessing2(male), times = 3) 

get_freq_table <- function(corpus_set) {
  corpus.pre <- preprocessing(corpus_set)
  all <- c()
  for (i in 1:length(corpus.pre)){
    all <- c(all, corpus.pre[[i]]$content)
  }
  return(table(all) %>% data.frame %>% arrange(desc(Freq)))
}

male.freq <- get_freq_table(male)
female.freq <- get_freq_table(female)
male.freq <- male.freq %>% rename(male.word=all, male.Freq=Freq)
female.freq <- female.freq %>% rename(female.word=all, female.Freq=Freq)
all.freq <- cbind_fill(male.freq, female.freq)

all.freq %>% head(50)
