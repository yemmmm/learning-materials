/** Export the built HTML as PDF using Playwright and an installed Chromium. */
const {chromium}=require('playwright');
const path=require('node:path');
const {pathToFileURL}=require('node:url');
(async()=>{
 const dir=path.resolve(__dirname,'../exports');
 const browser=await chromium.launch({headless:true,...(process.env.CHROMIUM_PATH?{executablePath:process.env.CHROMIUM_PATH}:{}),args:['--no-sandbox']});
 try{
  const page=await browser.newPage({viewport:{width:1920,height:1080}});
  await page.goto(pathToFileURL(path.join(dir,'llm-basics-slides-v0.10.html')).href,{waitUntil:'load'});
  await page.evaluate(()=>document.fonts.ready);
  await page.emulateMedia({media:'print',reducedMotion:'reduce'});
  await page.pdf({path:path.join(dir,'llm-basics-slides-v0.10.pdf'),preferCSSPageSize:true,printBackground:true,displayHeaderFooter:false,margin:{top:0,bottom:0,left:0,right:0}});
  console.log(`Exported ${await page.locator('.slide').count()} slides to PDF`);
 }finally{await browser.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
