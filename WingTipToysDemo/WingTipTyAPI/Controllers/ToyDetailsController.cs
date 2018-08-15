using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.WindowsAzure.Storage;
using Microsoft.WindowsAzure.Storage.Blob;
using WingTipToysEntities;

namespace WingTipToysAPI.Controllers
{
    [Route("api/[controller]")]
    [ApiController]
    public class ToyDetailsController : ControllerBase
    {
        string storageaccountConnectionString = "DefaultEndpointsProtocol=https;AccountName=myglstorageacc;AccountKey=Cu6yf47enl7a9UF1EVMhpeovCGNFw9DOatvyQEErBKH/1kAn7cq6LETKaTfCbQfvbbdUQCMCHXmigHV4Ag6h0w==;EndpointSuffix=core.windows.net";
        const string CDNUri = "https://ashraf-gl-storageendpoint-azurelab.azureedge.net";
        const string blobSASKey = "Cu6yf47enl7a9UF1EVMhpeovCGNFw9DOatvyQEErBKH/1kAn7cq6LETKaTfCbQfvbbdUQCMCHXmigHV4Ag6h0w==";

        // GET api/values
        [HttpGet]
        public async Task<ActionResult<IEnumerable<ToyDetailsViewModel>>> Get()
        {
            CloudStorageAccount storageAccount = CloudStorageAccount.Parse(storageaccountConnectionString);

            //Create a blob client
            var blobClient = storageAccount.CreateCloudBlobClient();
            var blobContainer = blobClient.GetContainerReference("myazurelabimages");

            await blobContainer.CreateIfNotExistsAsync();
            await blobContainer.SetPermissionsAsync(new BlobContainerPermissions
            {
                PublicAccess = BlobContainerPublicAccessType.Blob
            });

            BlobContinuationToken continuationToken = null;
            List<IListBlobItem> results = new List<IListBlobItem>();
            do
            {
                var response = await blobContainer.ListBlobsSegmentedAsync(continuationToken);
                continuationToken = response.ContinuationToken;
                results.AddRange(response.Results);
            }
            while (continuationToken != null);

            List<ToyDetailsViewModel> toyDetails = new List<ToyDetailsViewModel>();
            int i = 0;
            foreach (CloudBlob item in results)
            {
                var cdnUri = $"{CDNUri}/{item.Container.Name}/{item.Name}?sv={blobSASKey}";
                toyDetails.Add(new ToyDetailsViewModel { Image = cdnUri, Name= $"Item{++i}" });
               // toyDetails.Add(new ToyDetailsViewModel { Image = item.Uri.ToString(), Name = $"Item{++i}" });
            }
            return toyDetails;
        }
    }
}
