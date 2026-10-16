suppressPackageStartupMessages(library(metafor))
suppressPackageStartupMessages(library(metadat))
source('json17.R')
dir.create('documentation',showWarnings=FALSE)
ds <- sort(unique(data(package='metadat')[[ 'results', exact=TRUE]][,'Item']))
rd <- tools::Rd_db('metadat')
for(n in ds) {
 r <- rd[[paste0(n,'.Rd'),exact=TRUE]]
 if(!is.null(r)) {
  tools::Rd2ex(r,out=file.path('documentation',paste0(n,'.R')))
  tools::Rd2txt(r,out=file.path('documentation',paste0(n,'.txt')))
 }
}
tools::Rd2txt(tools::Rd_db('metafor')[[ 'gosh.Rd',exact=TRUE]],out='gosh-documentation.txt')
writeLines(deparse(metafor:::gosh.rma),'gosh-source.txt')
write_json17(list(R=R.version.string,metafor=as.character(packageVersion('metafor')),metadat=as.character(packageVersion('metadat')),meta=as.character(packageVersion('meta'))),'versions.json')
# Convert list extraction to exact indexing before executing copied/adapted recipes.
exact <- function(x) {
 if(is.call(x)) {
  if(as.character(x[[1]])[1] %in% c("<-","=","<<-") && is.call(x[[2]]) && identical(x[[2]][[1]],as.name("$"))) {
   lhs <- x[[2]]
   x[[2]] <- as.call(list(as.name("[["),exact(lhs[[2]]),as.character(lhs[[3]])))
   x[[3]] <- exact(x[[3]])
   return(x)
  }
  if(identical(x[[1]],as.name('$'))) return(as.call(list(as.name('[['),exact(x[[2]]),as.character(x[[3]]),exact=TRUE)))
  for(i in seq_along(x)) if(!identical(x[[i]],quote(expr=))) x[i] <- list(exact(x[[i]]))
 } else if(is.expression(x)) for(i in seq_along(x)) x[i] <- list(exact(x[[i]]))
 x
}
for(f in c('corpus-base.R','supplemental.R')) writeLines(vapply(exact(parse(f)),function(x)paste(deparse(x,width.cutoff=500),collapse='\n'),''),sub('.R$','-exact.R',f))
