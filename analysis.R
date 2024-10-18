library(magrittr)
library(dplyr)
library(stringr)
library(stopwords)
library(tm)
library(textstem)
library(microbenchmark)
library(str2str)

remove_except_kor <- function(x) gsub('[^가-힣]{1,}', ' ', x)
remove_padding <- function(x) gsub('\\s{1,}', ' ', x)
dirty_word <- 
  c('×같'='좆같', '×까'='좆까', '×나'='좆나', '×되'='좆되', '×밥'='좆밥', 
    '×랄'='지랄', '×발'='씨발', '×끼'='새끼', '×됐'='좆됐', '×새끼'='개새끼', 
    '×친'='미친', '개××'='개새끼', '씨×'='씨발', '새×'='새끼', '존×'='좆나', 
    '×신'='병신', '시×'='시발', '시×'='시발', '지×'='지랄', '병×'='병신', 
    '×시'='빙시', '×바'='시바', '×소리'='개소리', '×도'= '좆도', '걸레×'='걸레년',
    '개×'='개새끼', '걸×'='걸레', '개새×'='개새끼', '×레기'= '쓰레기', 
    '×빠지게'='좆빠지게')
# '×년'='썅년'
# '나쁜×' = '나쁜놈' or '미친년'
# '미친×'='미친놈' or '미친년'
unblind_dirty_word <-function(x) str_replace_all(x, dirty_word)

preprocessing <- function(vcorpus) vcorpus %>%
  tm_map(content_transformer(unblind_dirty_word)) %>%
  tm_map(content_transformer(remove_except_kor)) %>%
  tm_map(content_transformer(remove_padding)) %>%
  tm_map(content_transformer(str_trim))

export_text <- function(corpus, filepath) {
  corpus.pre <- preprocessing(corpus)
  sink(filepath)
  for (i in 1:length(corpus.pre)){
    cat(corpus.pre[[i]]$content[corpus.pre[[i]]$content != ''])
    cat("\n")
  }
  sink()
}




female <- VCorpus(DirSource("dataset/female"), readerControl=list(language='ko'))
male <- VCorpus(DirSource("dataset/male"), readerControl=list(language='ko'))



export_text(male, 'output/male.txt')
export_text(female, 'output/female.txt')





specialChars = '(ㆍ|「|】|、|…|」|”|』|“|『|＊|Ｌ|：|‥|《|※|》|，|。|ｌ|〉|【|\\|)'
removeSpecialChars <- function(x) gsub(specialChars, '', x)

get_freq_table <- function(corpus_set, only_kor) {
  if (only_kor)
    corpus.token <- preprocessing(corpus_set) %>% 
      tm_map(content_transformer(unblind_dirty_word)) %>%
      tm_map(content_transformer(scan_tokenizer))
  else
    corpus.token <- corpus_set %>% 
      tm_map(content_transformer(unblind_dirty_word)) %>%
      tm_map(removeNumbers) %>%
      tm_map(removePunctuation) %>%
      tm_map(content_transformer(removeSpecialChars)) %>%
      tm_map(content_transformer(scan_tokenizer))
  corpus.all <- c()
  for (i in 1:length(corpus.token)){
    corpus.all <- c(corpus.all, corpus.token[[i]]$content)
  }
  return(table(corpus.all) %>% data.frame %>% arrange(desc(Freq)))
}

export_freq_csv <- function(csv_path, only_kor) {
  male.freq <- get_freq_table(male, only_kor)
  female.freq <- get_freq_table(female, only_kor)
  male.freq <- male.freq %>% rename(male.word=corpus.all, male.Freq=Freq)
  female.freq <- female.freq %>% rename(female.word=corpus.all, female.Freq=Freq)
  all.freq <- cbind_fill(male.freq, female.freq)
  write.csv(all.freq, csv_path, row.names=FALSE)
}

export_freq_csv("output/freq_raw.csv", only_kor=FALSE)
export_freq_csv("output/freq.csv", only_kor=TRUE)


# stopwords::stopwords('ko', source='stopwords-iso')
# stopwords::stopwords('ko', source='marimo')
# microbenchmark(preprocessing(male), preprocessing2(male), times = 3) 
