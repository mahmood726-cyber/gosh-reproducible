suppressPackageStartupMessages(library(metafor))
source('analysis/json17.R')
args <- commandArgs(TRUE); shard <- as.integer(args[1]); nshard <- as.integer(args[2])
corpus <- readRDS('data/corpus.rds'); dir.create('.validate-work/reference',recursive=TRUE,showWarnings=FALSE)
get <- function(x,n) x[[n,exact=TRUE]]
for(ii in seq_along(corpus)) {
 if((ii-1)%%nshard != shard) next
 d <- corpus[[ii]]; k <- get(d,'k'); id <- get(d,'id'); yi <- get(d,'te'); vi <- get(d,'se')^2
 for(method in c('FE','DL')) {
  key <- paste(id,method,sep='::'); file <- file.path('.validate-work/reference',paste0(gsub(':','_',key,fixed=TRUE),'.json'))
  if(file.exists(file)) stop('Refusing stale reference output')
  start <- proc.time()[3]; warnings <- character(); errors <- list()
  ans <- tryCatch(withCallingHandlers({
   if(k>100) list(refused=TRUE,reason='page cap: more than 100 valid rows',points=list()) else {
    base <- rma(yi=yi,vi=vi,method=method)
    if(k<=15) {
     g <- gosh(base,progbar=FALSE)
     incl <- get(g,'incl'); res <- get(g,'res')
     points <- lapply(seq_len(nrow(incl)),function(j)list(members=which(incl[j,]),mu=get(res,'estimate')[j],I2=get(res,'I2')[j],Q=get(res,'QE')[j],tau2=get(res,'tau2')[j],k=get(res,'k')[j]))
    } else {
     memberfile <- file.path('.validate-work/memberships',paste0(gsub(':','_',key,fixed=TRUE),'.txt'))
     if(!file.exists(memberfile)) stop('Missing regenerated membership file')
     membership <- readLines(memberfile,warn=FALSE)
     points <- lapply(seq_along(membership),function(j){
      m <- as.integer(strsplit(membership[j],',',fixed=TRUE)[[1]])
      z <- tryCatch(rma(yi=yi[m],vi=vi[m],method=method),error=function(e)e)
      if(inherits(z,'error')) {errors[[length(errors)+1]] <<- list(draw=j,members=m,reason=conditionMessage(z));return(list(members=m,error=conditionMessage(z)))}
      list(members=m,mu=as.numeric(coef(z)),I2=get(z,'I2'),Q=get(z,'QE'),tau2=get(z,'tau2'),se=get(z,'se'),k=get(z,'k'))
     })
    }
    mus <- vapply(points,function(p)get(p,'mu'),0); i2 <- vapply(points,function(p)get(p,'I2'),0)
    list(refused=FALSE,points=points,summary=list(n_subsets=length(points),median_est=median(mus),median_i2=median(i2),min_est=min(mus),max_est=max(mus),q25_est=unname(quantile(mus,.25)),q75_est=unname(quantile(mus,.75))))
   }
  },warning=function(w){warnings <<- unique(c(warnings,conditionMessage(w)));invokeRestart('muffleWarning')}),error=function(e)list(refused=TRUE,reason=conditionMessage(e),points=list()))
  ans[['key']] <- key; ans[['warnings']] <- warnings; ans[['errors']] <- errors; ans[['seconds']] <- unname(proc.time()[3]-start)
  ans[['metafor_default']] <- list(exact=k<=19,n=if(k<=19)2^k-1 else 1e6)
  write_json17(ans,file)
  cat(key,':',length(get(ans,'points')),'subsets;',get(ans,'seconds'),'seconds\n');flush.console()
 }
}
