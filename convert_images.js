function toDataURL(src, callback, outputFormat) {
  let img = new Image();
  img.crossOrigin = 'Anonymous';
  img.onload = function() {
    let canvas = document.createElement('CANVAS');
    let ctx = canvas.getContext('2d');
    let dataURL;
    canvas.height = this.naturalHeight;
    canvas.width = this.naturalWidth;
    if(this.naturalWidth > 768){
      let mScale = 768/this.naturalWidth;
      ctx.scale(mScale, mScale);
    }
    ctx.drawImage(this, 0, 0);
    dataURL = canvas.toDataURL('image/jpeg');
    callback(dataURL);
  };
  img.src = src;
  if (img.complete || img.complete === undefined) {
    img.src = "data:image/gif;base64,R0lGODlhAQABAIAAAAAAAP///ywAAAAAAQABAAACAUwAOw==";
    img.src = src;
  }
}


all_images = document.querySelectorAll('img');
all_images.forEach(i=>{
    let src = i.src;
    toDataURL(src, x=>i.src=x);
});